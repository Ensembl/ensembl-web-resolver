from fastapi import APIRouter, Request
from typing import Optional, Literal
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.concurrency import run_in_threadpool
import logging
import re
from urllib.parse import quote

from app.api.error_response import response_error_handler
from app.api.metrics import record_resolver_outcome
from app.api.models.resolver import SearchPayload, StableIdResolverResponse
from app.api.utils.commons import build_stable_id_resolver_content, is_json_request
from app.api.utils.metadata import get_metadata
from app.api.utils.resolver import generate_resolver_id_page
from app.api.utils.search import get_search_results
from app.api.utils.legacy_url_resolver import ARCHIVE_HOSTS
from app.core.config import DEFAULT_APP
from app.core.logging import InterceptHandler

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()
MAIN_ARCHIVE_URL = f"https://{ARCHIVE_HOSTS['staging.ensembl.org']}"
STABLE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


@router.get("/{stable_id}", name="Resolver")
async def resolve(
    request: Request,
    stable_id: str,
    type: Optional[Literal["gene", "transcript", "protein"]] = None,
    gca: Optional[str] = "",
    app: Optional[Literal["genome-browser", "feature-explorer"]] = DEFAULT_APP,
):

    params = SearchPayload(stable_id=stable_id, type=type, per_page=10)
    response_mode = "json" if is_json_request(request) else "html"
    if not STABLE_ID_PATTERN.fullmatch(stable_id):
        record_resolver_outcome("stable_id", "invalid_request", response_mode)
        return response_error_handler(
            {"status": 400, "details": "Invalid stable ID format"}
        )

    try:
        # fm_py performs synchronous Redb file I/O. Run it off the async event
        # loop so concurrent resolver requests can continue to be served.
        search_results = await run_in_threadpool(get_search_results, params)

        if not search_results or not search_results.get("matches"):
            record_resolver_outcome("stable_id", "not_found", response_mode)
            if response_mode == "json":
                return response_error_handler({"status": 404})

            return RedirectResponse(
                f"{MAIN_ARCHIVE_URL}/id/{quote(stable_id, safe='')}", status_code=308
            )

        matches = search_results.get("matches")

        # Get metadata for all genomes
        metadata_results = get_metadata(matches)

        stable_id_resolver_response = StableIdResolverResponse(
            stable_id=stable_id,
            code=308,
        )
        results = build_stable_id_resolver_content(metadata_results)
        stable_id_resolver_response.content = results

        record_resolver_outcome("stable_id", "resolved", response_mode)
        if response_mode == "json":
            return results

        if len(results) == 1:
            if app == "feature-explorer":
                resolved_url = results[0].feature_explorer_url
            else:
                resolved_url = results[0].genome_browser_url
            return RedirectResponse(resolved_url)
        else:
            return HTMLResponse(generate_resolver_id_page(stable_id_resolver_response))
    except Exception as e:
        logging.error(f"Error: {e}")
        record_resolver_outcome("stable_id", "internal_error", response_mode)
        if response_mode == "json":
            return response_error_handler({"status": 500, "details": str(e)})
        res = StableIdResolverResponse(
            stable_id=stable_id, code=500, message=str(e), content=None
        )
        return HTMLResponse(generate_resolver_id_page(res))

from fastapi import APIRouter, Request
from typing import Optional, Literal
from fastapi.responses import RedirectResponse, HTMLResponse
import logging

from app.api.error_response import response_error_handler
from app.api.exceptions import EnsemblMetadataRequestError
from app.api.models.resolver import SearchPayload, StableIdResolverResponse
from app.api.utils.commons import build_stable_id_resolver_content, is_json_request
from app.api.utils.metadata import get_metadata
from app.api.utils.resolver import generate_resolver_id_page
from app.api.utils.search import get_search_results
from app.core.config import DEFAULT_APP
from app.core.logging import InterceptHandler

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()


@router.get("/{stable_id}", name="Resolver")
async def resolve(
    request: Request,
    stable_id: str,
    type: Optional[str] = "gene",
    gca: Optional[str] = "",
    app: Optional[Literal["genome-browser", "entity-viewer"]] = DEFAULT_APP,
):

    params = SearchPayload(stable_id=stable_id, type=type, per_page=10)
    search_results = get_search_results(params)

    if not search_results or not search_results.get("matches"):
        if is_json_request(request):
            return response_error_handler({"status": 404})

        res = StableIdResolverResponse(
            stable_id=stable_id,
            code=404,
            message="No results",
            content=None
        )
        return HTMLResponse(generate_resolver_id_page(res))

    try:
        matches = search_results.get("matches")

        # Get metadata for all genomes
        metadata_results = get_metadata(matches)

        stable_id_resolver_response = StableIdResolverResponse(
            stable_id=stable_id,
            code=308,
        )
        results = build_stable_id_resolver_content(metadata_results)
        stable_id_resolver_response.content = results

        if is_json_request(request):
            return results

        if len(results) == 1:
            if app == "entity-viewer":
                resolved_url = results[0].entity_viewer_url
            else:
                resolved_url = results[0].genome_browser_url
            return RedirectResponse(resolved_url)
        else:
            return HTMLResponse(generate_resolver_id_page(stable_id_resolver_response))
    except (EnsemblMetadataRequestError, Exception) as e:
        if is_json_request(request):
            return response_error_handler({"status": 500})
        res = StableIdResolverResponse(
            stable_id=stable_id,
            code=500,
            message=str(e),
            content=None
        )
        return HTMLResponse(generate_resolver_id_page(res))

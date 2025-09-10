from fastapi import APIRouter, Request
from typing import Optional, Literal, List
from fastapi.responses import RedirectResponse, HTMLResponse
import logging

from app.api.error_response import response_error_handler
from app.api.models.resolver import SearchPayload, StableIdResolverResponse, StableIdResolverContent
from app.api.utils.metadata import get_metadata
from app.api.utils.resolver import generate_resolver_id_page
from app.api.utils.search import get_search_results
from app.core.config import DEFAULT_APP, ENSEMBL_URL
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
        if "application/json" in request.headers.get("accept"):
            return response_error_handler({"status": 404})

        res = StableIdResolverResponse(
            stable_id=stable_id,
            code=404,
            message="No results",
            content=None
        )
        return HTMLResponse(generate_resolver_id_page(res))

    matches = search_results.get("matches")

    # Get metadata for all genomes
    metadata_results = get_metadata(matches)

    stable_id_resolver_response = StableIdResolverResponse(
        stable_id=stable_id,
        code=308,
    )
    results: List[StableIdResolverContent] = []

    for genome_id in metadata_results:
        metadata = metadata_results[genome_id]

        if not metadata:
            continue

        entity_viewer_url = f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{metadata['unversioned_stable_id']}"
        genome_browser_url = f"{ENSEMBL_URL}/genome-browser/{genome_id}?focus=gene:{metadata['unversioned_stable_id']}"
        content = StableIdResolverContent(
            entity_viewer_url=entity_viewer_url,
            genome_browser_url=genome_browser_url,
            **metadata,
        )
        results.append(content)

    stable_id_resolver_response.content = results

    if "application/json" in request.headers.get("accept"):
        return results

    if len(results) == 1:
        if app == "entity-viewer":
            resolved_url = results[0].entity_viewer_url
        else:
            resolved_url = results[0].genome_browser_url
        return RedirectResponse(resolved_url)
    else:
        return HTMLResponse(generate_resolver_id_page(stable_id_resolver_response.model_dump()))

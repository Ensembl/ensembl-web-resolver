from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Query, HTTPException

from starlette.responses import HTMLResponse
from starlette.concurrency import run_in_threadpool

import logging

from app.api.error_response import response_error_handler
from app.api.metrics import record_resolver_outcome
from app.api.models.resolver import (
    RapidResolverResponse,
    RapidResolverHtmlResponseType,
    SearchPayload,
    StableIdResolverResponse,
)
from app.api.utils.commons import build_stable_id_resolver_content, is_json_request
from app.api.utils.metadata import (
    get_genome_id_from_assembly_accession_id,
    get_metadata,
)
from app.api.utils.rapid import (
    format_assembly_accession,
    construct_url,
    generate_rapid_id_page,
    generate_rapid_page,
    construct_rapid_archive_url,
)
from app.api.utils.search import get_search_results
from app.core.config import ENSEMBL_URL
from app.core.logging import InterceptHandler

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()


@router.get("/id/{stable_id}", name="Resolve rapid stable ID")
async def resolve_rapid_stable_id(request: Request, stable_id: str):
    # Handle only gene stable id for now
    params = SearchPayload(stable_id=stable_id, type="gene", per_page=10)
    rapid_archive_url = construct_rapid_archive_url(request)
    response_mode = "json" if is_json_request(request) else "html"

    try:
        # fm_py performs synchronous Redb file I/O. Run it off the async event
        # loop so concurrent resolver requests can continue to be served.
        search_results = await run_in_threadpool(get_search_results, params)

        if not search_results or not search_results.get("matches"):
            record_resolver_outcome("rapid_stable_id", "not_found", response_mode)
            if response_mode == "json":
                return response_error_handler({"status": 404})
            res = StableIdResolverResponse(
                stable_id=stable_id,
                code=404,
                message="No results",
                content=None,
                rapid_archive_url=rapid_archive_url,
            )
            return HTMLResponse(generate_rapid_id_page(res))

        matches = search_results.get("matches")
        metadata_results = get_metadata(matches)

        stable_id_resolver_response = StableIdResolverResponse(
            stable_id=stable_id, code=308, rapid_archive_url=rapid_archive_url
        )
        results = build_stable_id_resolver_content(metadata_results)
        stable_id_resolver_response.content = results

        record_resolver_outcome("rapid_stable_id", "resolved", response_mode)
        if response_mode == "json":
            return results

        return HTMLResponse(generate_rapid_id_page(stable_id_resolver_response))
    except Exception as e:
        logging.error(f"Error: {e}")
        record_resolver_outcome("rapid_stable_id", "internal_error", response_mode)
        if response_mode == "json":
            return response_error_handler({"status": 500, "details": str(e)})
        res = StableIdResolverResponse(
            stable_id=stable_id,
            code=500,
            message=str(e),
            content=None,
            rapid_archive_url=rapid_archive_url,
        )
        return HTMLResponse(generate_rapid_id_page(res))


@router.get("/info/{subpath:path}", name="Resolve rapid help page")
async def resolve_rapid_help(request: Request, subpath: str = ""):
    response = RapidResolverResponse(
        response_type=RapidResolverHtmlResponseType.HELP,
        code=308,
        resolved_url=f"{ENSEMBL_URL}/help",
        rapid_archive_url=construct_rapid_archive_url(request),
    )
    return rapid_resolved_response(response, request)


@router.get("/Multi/Tools/Blast", name="Resolve rapid blast page")
async def resolve_rapid_blast(request: Request):
    response = RapidResolverResponse(
        response_type=RapidResolverHtmlResponseType.BLAST,
        code=308,
        resolved_url=f"{ENSEMBL_URL}/blast",
        rapid_archive_url=construct_rapid_archive_url(request),
    )
    return rapid_resolved_response(response, request)


# Resolve rapid urls
@router.get("/{species_url_name}", name="Rapid Species Resources")
@router.get("/{species_url_name}/{subpath:path}", name="Rapid Species Resources")
async def resolve_species(
    request: Request, species_url_name: str, subpath: str = "", r: str = Query(None)
):
    rapid_archive_url = construct_rapid_archive_url(request)
    # Check if its blast redirect
    if "tools/blast" in subpath.lower():
        response = RapidResolverResponse(
            response_type=RapidResolverHtmlResponseType.BLAST,
            code=308,
            resolved_url=f"{ENSEMBL_URL}/blast",
            species_name=species_url_name,
            rapid_archive_url=rapid_archive_url,
        )
        return rapid_resolved_response(response, request)

    try:
        assembly_accession_id = format_assembly_accession(species_url_name)

        if assembly_accession_id is None:
            raise HTTPException(
                status_code=422, detail="Invalid input accession ID"
            )

        genome_object = get_genome_id_from_assembly_accession_id(assembly_accession_id)

        if genome_object and genome_object != {}:
            genome_id = genome_object["genome_tag"] or genome_object["genome_uuid"]

            # Extract specific parameters because Ensembl url uses ; instead of &
            query_string = request.scope["query_string"].decode()
            query_params = parse_qs(query_string, separator=";")

            url = construct_url(genome_id, subpath, query_params)
            response = RapidResolverResponse(
                response_type=RapidResolverHtmlResponseType.INFO,
                code=308,
                resolved_url=url,
                species_name=species_url_name,
                gene_id=query_params.get("g", [None])[0],
                location=query_params.get("r", [None])[0],
                rapid_archive_url=rapid_archive_url,
            )
            return rapid_resolved_response(response, request)
        else:
            raise HTTPException(status_code=404, detail="Genome not found")
    except HTTPException as e:
        logging.error(f"HTTP Error: {e.detail}")
        response = RapidResolverResponse(
            response_type=RapidResolverHtmlResponseType.ERROR,
            code=e.status_code,
            resolved_url=f"{ENSEMBL_URL}/genome-selector",
            message=e.detail,
            species_name=species_url_name,
            rapid_archive_url=rapid_archive_url,
        )
        return rapid_resolved_response(response, request)
    except Exception as e:
        logging.error(f"Error: {e}")
        response = RapidResolverResponse(
            species_name=species_url_name,
            response_type=RapidResolverHtmlResponseType.ERROR,
            code=500,
            resolved_url=f"{ENSEMBL_URL}/genome-selector",
            message=str(e),
            rapid_archive_url=rapid_archive_url,
        )
        return rapid_resolved_response(response, request)


@router.get("/", name="Rapid Home")
async def resolve_home(request: Request):
    response = RapidResolverResponse(
        response_type=RapidResolverHtmlResponseType.HOME,
        code=308,
        resolved_url=ENSEMBL_URL,
        rapid_archive_url=construct_rapid_archive_url(request),
    )
    return rapid_resolved_response(response, request)


def rapid_resolved_response(response: RapidResolverResponse, request: Request):
    response_mode = "json" if is_json_request(request) else "html"
    if response.response_type == RapidResolverHtmlResponseType.ERROR:
        outcome = (
            "invalid_request"
            if response.code == 422
            else "not_found"
            if response.code == 404
            else "internal_error"
        )
    else:
        outcome = "resolved"
    record_resolver_outcome("rapid", outcome, response_mode)

    if response_mode == "json":
        if response.response_type == RapidResolverHtmlResponseType.ERROR:
            raise HTTPException(
                status_code=response.code,
                detail=response.message or "An error occurred",
            )
        return response.model_dump()
    return HTMLResponse(generate_rapid_page(response))

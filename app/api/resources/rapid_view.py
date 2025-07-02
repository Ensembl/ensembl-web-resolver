from urllib.parse import parse_qs
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import RedirectResponse
import logging
from api.models.resolver import ResolvedURLResponse
from core.logging import InterceptHandler
from core.config import ENSEMBL_URL
from api.utils.metadata import get_genome_id_from_assembly_accession_id
from api.utils.rapid import construct_url, format_assembly_accession

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()


@router.get("/info/{subpath:path}", name="Resolve rapid help page")
async def resolve_rapid_help(request: Request, subpath: str = ""):
    help_page_url = f"{ENSEMBL_URL}/help"
    return resolved_response(help_page_url, request)


@router.get("/Blast", name="Resolve rapid blast page")
async def resolve_rapid_blast(request: Request):
    blast_page_url = f"{ENSEMBL_URL}/blast"
    return resolved_response(blast_page_url, request)


# Resolve rapid urls
@router.get("/{species_url_name}", name="Rapid Species Resources")
@router.get("/{species_url_name}/{subpath:path}", name="Rapid Species Resources")
async def resolve_species(
    request: Request, species_url_name: str, subpath: str = "", r: str = Query(None)
):
    assembly_accession_id = format_assembly_accession(species_url_name)

    if assembly_accession_id is None:
        raise HTTPException(
            status_code=422, detail="Unable to process input accession ID"
        )
    try:
        genome_object = get_genome_id_from_assembly_accession_id(assembly_accession_id)

        if genome_object and genome_object != {}:
            genome_id = genome_object["genome_tag"] or genome_object["genome_uuid"]

            # Extract specific parameters because Ensembl url uses ; instead of &
            query_string = request.scope["query_string"].decode()
            query_params = parse_qs(query_string, separator=";")

            url = construct_url(genome_id, subpath, query_params)
            return resolved_response(url, request)
        else:
            raise HTTPException(status_code=404, detail="Genome not found")

    except HTTPException as e:
        logging.debug(e)
        raise HTTPException(
            status_code=e.status_code, detail="Unexpected error occured"
        )

    except Exception as e:
        logging.debug(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


@router.get("/", name="Rapid Home")
async def resolve_home(request: Request):
    return resolved_response(ENSEMBL_URL, request)


def resolved_response(url: str, request: Request):
    if "application/json" in request.headers.get("accept"):
        return ResolvedURLResponse(resolved_url=url)
    return RedirectResponse(url)

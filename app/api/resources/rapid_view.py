import os
from urllib.parse import parse_qs

from dotenv import load_dotenv
from fastapi import APIRouter, Request, Query, HTTPException

from jinja2 import Environment, FileSystemLoader
from starlette.responses import HTMLResponse

import logging
from api.models.resolver import ResolvedURLResponse, RapidRedirectResponseType
from core.logging import InterceptHandler
from core.config import ENSEMBL_URL
from api.utils.metadata import get_genome_id_from_assembly_accession_id
from api.utils.rapid import construct_url, format_assembly_accession

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()


@router.get("/info/{subpath:path}", name="Resolve rapid help page")
async def resolve_rapid_help(request: Request, subpath: str = ""):
    response = ResolvedURLResponse(
        response_type=RapidRedirectResponseType.HELP,
        code=308,
        resolved_url=f"{ENSEMBL_URL}/help",
    )
    return resolved_response(response, request)


@router.get("/Blast", name="Resolve rapid blast page")
async def resolve_rapid_blast(request: Request):
    response = ResolvedURLResponse(
        response_type=RapidRedirectResponseType.BLAST,
        code=308,
        resolved_url=f"{ENSEMBL_URL}/blast",
    )
    return resolved_response(response, request)


# Resolve rapid urls
@router.get("/{species_url_name}", name="Rapid Species Resources")
@router.get("/{species_url_name}/{subpath:path}", name="Rapid Species Resources")
async def resolve_species(
    request: Request, species_url_name: str, subpath: str = "", r: str = Query(None)
):
    assembly_accession_id = format_assembly_accession(species_url_name)

    if assembly_accession_id is None:
        input_error_response = ResolvedURLResponse(
            response_type=RapidRedirectResponseType.ERROR,
            code=422,
            resolved_url=ENSEMBL_URL,
            message="Invalid input accession ID",
            species_name=species_url_name,
        )
        return resolved_response(input_error_response, request)

    try:
        genome_object = get_genome_id_from_assembly_accession_id(assembly_accession_id)

        if genome_object and genome_object != {}:
            genome_id = genome_object["genome_tag"] or genome_object["genome_uuid"]

            # Extract specific parameters because Ensembl url uses ; instead of &
            query_string = request.scope["query_string"].decode()
            query_params = parse_qs(query_string, separator=";")

            url = construct_url(genome_id, subpath, query_params)
            response = ResolvedURLResponse(
                response_type=RapidRedirectResponseType.INFO,
                code=308,
                resolved_url=url,
                species_name=species_url_name,
                gene_id=query_params.get("g", [None])[0],
                location=query_params.get("r", [None])[0],
            )
            return resolved_response(response, request)
        else:
            raise HTTPException(status_code=404, detail="Genome not found")
    except HTTPException as e:
        logging.debug(e)
        response = ResolvedURLResponse(
            response_type=RapidRedirectResponseType.ERROR,
            code=e.status_code,
            resolved_url=ENSEMBL_URL,
            message=e.detail,
            species_name=species_url_name,
        )
        return resolved_response(response, request)
    except Exception as e:
        logging.debug(f"Unexpected error occurred: {e}")
        response = ResolvedURLResponse(
            response_type=RapidRedirectResponseType.ERROR,
            code=500,
            resolved_url=ENSEMBL_URL,
            message="Unexpected error occurred",
        )
        return resolved_response(response, request)


@router.get("/", name="Rapid Home")
async def resolve_home(request: Request):
    response = ResolvedURLResponse(
        response_type=RapidRedirectResponseType.HOME,
        code=308,
        resolved_url=ENSEMBL_URL,
    )
    return resolved_response(response, request)


def resolved_response(response: ResolvedURLResponse, request: Request):
    if "application/json" in request.headers.get("accept"):
        if response.response_type == RapidRedirectResponseType.ERROR:
            raise HTTPException(
                status_code=response.code,
                detail=response.message or "An error occurred",
            )
        return ResolvedURLResponse(resolved_url=response.resolved_url)
    return HTMLResponse(generate_html_content(response))


def generate_html_content(response):
    load_dotenv()
    CURR_DIR = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(os.path.join(CURR_DIR, "templates/rapid")))
    rapid_redirect_page_template = env.get_template("main.html")
    rapid_redirect_page_html = rapid_redirect_page_template.render(response=response)
    return rapid_redirect_page_html

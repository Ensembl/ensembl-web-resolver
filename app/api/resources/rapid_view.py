from urllib.parse import parse_qs
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import RedirectResponse
import logging
import re
from core.logging import InterceptHandler
from core.config import ENSEMBL_URL
from api.utils.metadata import get_genome_id_from_assembly_accession_id
from api.utils.rapid import format_assembly_accession

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()


# Resolve rapid urls
@router.get("/{species_url_name}", name="Rapid Species Home")
@router.get("/{species_url_name}/", name="Rapid Species Home")
@router.get("/{species_url_name}/{subpath:path}", name="Rapid Species Home")
async def resolve_species(
    request: Request, species_url_name: str, subpath: str = "", r: str = Query(None)
):

    assembly_accession_id = format_assembly_accession(species_url_name)

    genome_object = get_genome_id_from_assembly_accession_id(assembly_accession_id)

    if genome_object:
        genome_id = genome_object["genome_tag"] or genome_object["genome_uuid"]

        # Extract specific parameters because Ensembl url uses ; instead of &
        raw_query_string = request.scope["query_string"].decode()
        query_string = raw_query_string.replace(";", "&")
        query_params = parse_qs(query_string)

        r = query_params.get("r", [None])[0]
        g = query_params.get("g", [None])[0]

        if subpath == "":
            url = f"{ENSEMBL_URL}/species/{genome_id}"
        elif re.search("Location", subpath):
            url = f"{ENSEMBL_URL}/genome-browser/{genome_id}?focus=location:{r}"
        elif re.search("Gene", subpath):
            if re.search("Gene/Compara_Homolog", subpath):
                url = f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{g}?view=homology"
            else:
                url = f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{g}"

        elif re.search("Transcript", subpath):
            if re.search("Domains|ProteinSummary", subpath):
                url = f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{g}?view=protein"
            else:
                url = f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{g}"
        else:
            url = ENSEMBL_URL

        return RedirectResponse(url)

    else:
        raise HTTPException(status_code=404, detail="Genome not found")


@router.get("/", name="Rapid Home")
async def resolve_home(request: Request):
    return RedirectResponse(ENSEMBL_URL)

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
@router.get("/{species_url_name}", name="Rapid Species Resources")
@router.get("/{species_url_name}/", name="Rapid Species Resources")
@router.get("/{species_url_name}/{subpath:path}", name="Rapid Species Resources")
async def resolve_species(
    request: Request, species_url_name: str, subpath: str = "", r: str = Query(None)
):
    assembly_accession_id = format_assembly_accession(species_url_name)

    if assembly_accession_id is None:
        raise HTTPException(
            status_code=422, detail="Unable to process input accession ID"
        )

    genome_object = get_genome_id_from_assembly_accession_id(assembly_accession_id)

    if genome_object:
        genome_id = genome_object["genome_tag"] or genome_object["genome_uuid"]

        # Extract specific parameters because Ensembl url uses ; instead of &
        query_string = request.scope["query_string"].decode()
        query_params = parse_qs(query_string, separator=";")

        location = query_params.get("r", [None])[0]
        gene_id = query_params.get("g", [None])[0]

        if subpath == "" or re.search("Info/Index", subpath, re.IGNORECASE):
            url = f"{ENSEMBL_URL}/species/{genome_id}"
        elif re.search("Location", subpath):
            url = f"{ENSEMBL_URL}/genome-browser/{genome_id}?focus=location:{location}"
        elif re.search("Gene", subpath):
            if re.search("Gene/Compara_Homolog", subpath):
                url = (
                    f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}"
                    f"?view=homology"
                )
            else:
                url = f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}"

        elif re.search("Transcript", subpath):
            if re.search("Domains|ProteinSummary", subpath):
                url = (
                    f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}"
                    f"?view=protein"
                )
            else:
                url = f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}"
        else:
            url = ENSEMBL_URL

        return RedirectResponse(url)

    else:
        raise HTTPException(status_code=404, detail="Genome not found")


@router.get("/", name="Rapid Home")
async def resolve_home(request: Request):
    return RedirectResponse(ENSEMBL_URL)

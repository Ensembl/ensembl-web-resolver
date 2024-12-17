from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import logging
import re
from core.logging import InterceptHandler
from core.config import ENSEMBL_URL
from api.utils.metadata import get_genome_id_from_assembly_accession_id

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()


# Resolve species home
# https://rapid.ensembl.org/Homo_sapiens_GCA_009914755.4/
# https://rapid.ensembl.org/Homo_sapiens_GCA_009914755.4/Info/Index
@router.get("/{species_url_name}/{subpath:path}", name="Rapid Species Home")
async def resolve_species(request: Request, species_url_name: str, subpath: str):
    if re.search("_GCA_", species_url_name):
        _, accession_id = species_url_name.split("_GCA_")
    else:
        logging.error("Genome url name missing GCA assembly accession id")
        raise HTTPException(
            status_code=400, detail="Genome url name missing GCA assembly accession id"
        )

    assembly_accession_id = "GCA_" + accession_id

    # RefSeqs have GCF prefix
    if accession_id.endswith("rs"):
        accession_id, _ = re.split(r"rs$", accession_id)
        assembly_accession_id = "GCF_" + accession_id

    genome_object = get_genome_id_from_assembly_accession_id(assembly_accession_id)
    if genome_object:
        genome_id = genome_object.get("genomeUuid")
        url = f"{ENSEMBL_URL}/species/{genome_id}"
        return RedirectResponse(url)
    else:
        raise HTTPException(status_code=404, detail="Genome not found")


@router.get("/", name="Rapid Home")
async def resolve_home(request: Request):
    return RedirectResponse(ENSEMBL_URL)

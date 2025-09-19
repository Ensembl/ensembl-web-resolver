import os

from jinja2 import Environment, FileSystemLoader
from loguru import logger
from fastapi import Request
import requests
import re

from app.core.config import NCBI_DATASETS_URL, ENSEMBL_URL, RAPID_ARCHIVE_URL


def get_assembly_accession_from_ncbi(accession_id: str):
    try:
        session = requests.Session()
        ncbi_dataset_api_url = (
            f"{NCBI_DATASETS_URL}/genome/accession/{accession_id}/dataset_report"
        )

        with session.get(url=ncbi_dataset_api_url, timeout=10) as response:
            response.raise_for_status()
            response_json = response.json()
            if response_json and response_json["reports"]:
                return response_json["reports"][0]
            else:
                return None
    except Exception:
        raise Exception("Failed to fetch data from NCBI")


def format_assembly_accession(species_url_name: str):
    if re.search("_GCA_|_GCF_", species_url_name):
        _, accession_id = re.split("_GCA_|_GCF_", species_url_name)

        prefix = "GCA_"
        if re.search("GCF", species_url_name):
            prefix = "GCF_"

        assembly_accession_id = prefix + accession_id

        # RefSeqs have GCF prefix but version could be different. So fetch it from ncbi
        if assembly_accession_id.endswith("rs"):
            trimmed_assembly_accession_id = re.sub("rs$", "", assembly_accession_id)
            ncbi_dataset_report = get_assembly_accession_from_ncbi(
                trimmed_assembly_accession_id
            )

            if ncbi_dataset_report:
                assembly_accession_id = ncbi_dataset_report["paired_accession"]
            else:
                logger.error("HTTPError: {HTTPError}")
                return None
        return assembly_accession_id
    else:
        return None


def construct_url(genome_id, subpath, query_params):
    location = query_params.get("r", [None])[0]
    gene_id = query_params.get("g", [None])[0]

    subpath = subpath or ""
    subpath_lower = subpath.lower()

    if genome_id is None:
        return ENSEMBL_URL

    if not subpath or "info/index" in subpath_lower:
        return f"{ENSEMBL_URL}/species/{genome_id}"

    if "location" in subpath_lower:
        if "genome" in subpath_lower:
            return f"{ENSEMBL_URL}/species/{genome_id}"
        if location is None:
            raise ValueError("Location paramater 'r' is missing for Location view")
        return f"{ENSEMBL_URL}/genome-browser/{genome_id}?focus=location:{location}"

    if "gene" in subpath_lower:
        if not gene_id:
            raise ValueError("Gene parameter 'g' is missing for Gene view")
        if "compara_homolog" in subpath_lower:
            return f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}?view=homology"
        return f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}"

    if "transcript" in subpath_lower:
        if not gene_id:
            raise ValueError("Gene parameter 'g' is missing for Transcript view")
        if "domains" in subpath_lower or "proteinsummary" in subpath_lower:
            return f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}?view=protein"
        return f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}"

    raise ValueError("Invalid path")


def construct_rapid_archive_url(request: Request):
    try:
        rapid_archive_path = request.url.path.removeprefix("/rapid/")
        if not rapid_archive_path:
            return RAPID_ARCHIVE_URL

        if request.url.query:
            rapid_archive_path = f"{rapid_archive_path}?{request.url.query}"

        return f"{RAPID_ARCHIVE_URL}/{rapid_archive_path}"
    except Exception as e:
        logger.warning(f"Error constructing rapid archive url: {e}")
        return RAPID_ARCHIVE_URL


def generate_html_content(response, page):
    templates_path = os.path.join(os.path.dirname(__file__), "../resources/templates")
    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template(f"rapid/{page}")
    content = template.render(response=response)
    return content


def generate_rapid_page(response):
    return generate_html_content(response, "rapid.html")


def generate_rapid_id_page(response):
    return generate_html_content(response, "rapid_id.html")

from loguru import logger
import requests
from core.config import ENSEMBL_URL, NCBI_DATASETS_URL
import re


def get_assembly_accession_from_ncbi(accession_id: str):
    try:
        session = requests.Session()
        ncbi_dataset_api_url = (
            f"{NCBI_DATASETS_URL}/genome/accession/{accession_id}/dataset_report"
        )

        with session.get(url=ncbi_dataset_api_url) as response:
            response.raise_for_status()
            response_json = response.json()
            if response_json and response_json["reports"]:
                return response_json["reports"][0]
            else:
                return None

    except requests.exceptions.HTTPError as HTTPError:
        logger.error(f"HTTPError: {HTTPError}")
        raise HTTPError
    except Exception as e:
        logger.exception(e)
        raise e


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

    if subpath == "" or re.search("Info/Index", subpath, re.IGNORECASE):
        return f"{ENSEMBL_URL}/species/{genome_id}"
    elif re.search("Location", subpath):
        return f"{ENSEMBL_URL}/genome-browser/{genome_id}?focus=location:{location}"
    elif re.search("Gene", subpath):
        if re.search("Gene/Compara_Homolog", subpath):
            return (
                f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}?view=homology"
            )
        return f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}"
    elif re.search("Transcript", subpath):
        if re.search("Domains|ProteinSummary", subpath):
            return (
                f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}?view=protein"
            )
        return f"{ENSEMBL_URL}/entity-viewer/{genome_id}/gene:{gene_id}"
    return ENSEMBL_URL

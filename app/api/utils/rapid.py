from loguru import logger
import requests
from core.config import NCBI_DATASETS_URL
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

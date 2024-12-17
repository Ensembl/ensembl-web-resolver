from loguru import logger
import requests
from typing import List
from core.config import ENSEMBL_URL
from api.models.resolver import SearchMatch


def get_metadata(matches: List[SearchMatch] = []):

    metadata_results = {}

    for match in matches:
        genome_id = match.get("genome_id")
        try:
            session = requests.Session()
            with session.get(
                url=f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/details"
            ) as response:
                response.raise_for_status()
                metadata_results[genome_id] = response.json()
                metadata_results[genome_id]["unversioned_stable_id"] = match.get(
                    "unversioned_stable_id"
                )
        except requests.exceptions.HTTPError as HTTPError:
            logger.error(f"HTTPError: {HTTPError}")
            return None
        except Exception as e:
            logger.exception(e)
            return None

    return metadata_results


def get_genome_id_from_assembly_accession_id(accession_id: str):
    try:
        session = requests.Session()
        metadata_api_url = (
            f"{ENSEMBL_URL}/api/metadata/genome?assembly_accession_id={accession_id}"
        )
        with session.get(url=metadata_api_url) as response:
            response.raise_for_status()
            response_json = response.json()
            return response_json
    except requests.exceptions.HTTPError as HTTPError:
        logger.error(f"HTTPError: {HTTPError}")
        return None
    except Exception as e:
        logger.exception(e)
        return None

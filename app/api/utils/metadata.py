import requests
from typing import List

from app.api.models.resolver import SearchMatch
from app.core.config import ENSEMBL_URL


def get_metadata(matches: List[SearchMatch] = []):

    metadata_results = {}

    for match in matches:
        genome_id = match.get("genome_id")
        try:
            session = requests.Session()
            with session.get(
                url=f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/details",
                timeout=10
            ) as response:
                response.raise_for_status()
                metadata_results[genome_id] = response.json()
                metadata_results[genome_id]["unversioned_stable_id"] = match.get(
                    "unversioned_stable_id"
                )
        except Exception:
            raise Exception("Failed to fetch data from metadata service")

    return metadata_results


def get_genome_id_from_assembly_accession_id(accession_id: str):
    try:
        session = requests.Session()
        metadata_api_url = (
            f"{ENSEMBL_URL}/api/metadata/genomeid?assembly_accession_id={accession_id}"
        )
        with session.get(url=metadata_api_url, timeout=10) as response:
            response.raise_for_status()
            return response.json()
    except Exception:
        raise Exception("Failed to fetch data from metadata service")

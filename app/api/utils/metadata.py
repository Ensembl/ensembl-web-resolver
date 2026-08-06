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
                url=f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/details", timeout=10
            ) as response:
                response.raise_for_status()
                metadata_results[genome_id] = response.json()
                metadata_results[genome_id]["unversioned_stable_id"] = match.get(
                    "unversioned_stable_id"
                )
        except Exception as e:
            raise Exception(
                f"Failed to fetch metadata for genome '{genome_id}': {e}"
            ) from e

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
    except Exception as e:
        raise Exception(
            f"Failed to fetch genome ID for assembly accession '{accession_id}': {e}"
        ) from e


def get_genome_tag_from_genome_id(genome_id: str) -> str | None:
    """Fetch the genome tag for a current Ensembl genome ID.

    Args:
        genome_id: Current Ensembl genome UUID.

    Returns:
        The genome tag, or ``None`` when the genome has no tag.

    Raises:
        Exception: If the metadata explain endpoint cannot be queried or decoded.
    """
    try:
        session = requests.Session()
        metadata_api_url = f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/explain"
        with session.get(url=metadata_api_url, timeout=10) as response:
            response.raise_for_status()
            payload = response.json()

        genome_tag = payload.get("genome_tag") if isinstance(payload, dict) else None
        return genome_tag or None
    except Exception as error:
        raise Exception(
            f"Failed to fetch genome tag for genome '{genome_id}': {error}"
        ) from error


def search_variant(genome_id: str, variant_id: str) -> dict | None:
    """Find a variant in a genome through the Ensembl variant search API."""
    try:
        session = requests.Session()
        with session.post(
            url=f"{ENSEMBL_URL}/api/search/variants",
            json={"genome_ids": [genome_id], "query": variant_id},
            timeout=10,
        ) as response:
            response.raise_for_status()
            payload = response.json()

        matches = payload.get("matches") if isinstance(payload, dict) else None
        if not isinstance(matches, list) or not matches:
            return None

        first_match = matches[0]
        return first_match if isinstance(first_match, dict) else None
    except Exception as error:
        raise Exception(
            f"Failed to search for variant '{variant_id}' in genome '{genome_id}': {error}"
        ) from error

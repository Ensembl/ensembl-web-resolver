import requests
import re
from typing import List

from app.api.models.resolver import SearchMatch
from app.core.config import ENSEMBL_URL


class MetadataNotFoundError(Exception):
    """Raised when a requested genome is absent from the metadata API."""


def get_metadata(matches: List[SearchMatch] = []):
    type_priority = {"gene": 0, "transcript": 1, "protein": 2}
    matches_by_genome = {}

    for match in matches:
        genome_id = match.get("genome_id")
        current_match = matches_by_genome.get(genome_id)
        if current_match is None or type_priority.get(
            match.get("type") or match.get("doc_type") or "gene", 0
        ) < type_priority.get(
            current_match.get("type") or current_match.get("doc_type") or "gene", 0
        ):
            matches_by_genome[genome_id] = match

    metadata_results = {}

    for match in matches_by_genome.values():
        genome_id = match.get("genome_id")
        try:
            session = requests.Session()
            with session.get(
                url=f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/explain", timeout=10
            ) as response:
                response.raise_for_status()
                metadata_results[genome_id] = response.json()
                metadata_results[genome_id]["unversioned_stable_id"] = match.get(
                    "unversioned_stable_id"
                )
                # Fast-match supplies this field. Keep the historical gene
                # default for search-hub responses that do not yet include it.
                metadata_results[genome_id]["stable_id_type"] = (
                    match.get("type") or match.get("doc_type") or "gene"
                )
                metadata_results[genome_id]["parent_transcript_id"] = match.get(
                    "parent_transcript_id"
                )
        except Exception as e:
            raise Exception(
                f"Failed to fetch metadata for genome '{genome_id}': {e}"
            ) from e

    return _filter_metadata_releases(metadata_results)


def _filter_metadata_releases(metadata_results):
    """Keep the newest integrated release for each assembly.

    Partial and archive releases are retained only when an assembly has no
    integrated release available. This allows distinct assemblies such as
    GRCh37 and GRCh38 to remain visible.
    """
    by_assembly = {}
    for genome_id, metadata in metadata_results.items():
        assembly = metadata.get("assembly") or {}
        assembly_key = assembly.get("accession_id") or assembly.get("name") or genome_id
        by_assembly.setdefault(assembly_key, []).append((genome_id, metadata))

    filtered = {}
    for releases in by_assembly.values():
        integrated = [
            release
            for release in releases
            if (release[1].get("release") or {}).get("type") == "integrated"
        ]
        candidates = integrated or releases
        genome_id, metadata = max(
            candidates,
            key=lambda release: _release_sort_key(release[1]),
        )
        filtered[genome_id] = metadata

    return filtered


def _release_sort_key(metadata):
    """Build a sortable key so the newest release can be selected.

    Release names normally contain an ISO-like date such as ``2026-07`` or
    ``2026-04-09``. These components are converted to numbers and compared in
    year/month/day order. The leading ``1`` makes dated releases sort after
    undated names; the release name is retained as a final deterministic
    tie-breaker.
    """
    release_name = str((metadata.get("release") or {}).get("name") or "")
    date_match = re.search(r"(\d{4})-(\d{2})(?:-(\d{2}))?", release_name)
    if date_match:
        year, month, day = date_match.groups()
        # Missing days represent a month-level release and sort before any
        # dated release in that same month.
        return (1, int(year), int(month), int(day or 0), release_name)
    # Keep undated releases usable as a fallback, but rank them below dated
    # releases when both forms are available.
    return (0, 0, 0, 0, release_name)


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
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            raise MetadataNotFoundError(
                f"Genome '{genome_id}' was not found in the metadata API"
            ) from error
        raise Exception(
            f"Failed to fetch genome tag for genome '{genome_id}': {error}"
        ) from error
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
    except requests.HTTPError as error:
        # The variants endpoint uses 404 to indicate that a query has no match.
        # Treat this the same as an empty ``matches`` list so the legacy
        # resolver can return its normal 404 response.
        if error.response is not None and error.response.status_code == 404:
            return None
        raise Exception(
            f"Failed to search for variant '{variant_id}' in genome '{genome_id}': {error}"
        ) from error
    except Exception as error:
        raise Exception(
            f"Failed to search for variant '{variant_id}' in genome '{genome_id}': {error}"
        ) from error

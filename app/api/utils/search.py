import re

import requests
from loguru import logger

try:
    import fm_py
except ImportError:
    fm_py = None

from app.api.models.resolver import SearchPayload
from app.core.config import (
    ENSEMBL_SEARCH_HUB_API,
    FAST_MATCH_DB_PATH,
    FAST_MATCH_ENABLED,
)


def get_search_results(params: SearchPayload):
    if not FAST_MATCH_ENABLED:
        logger.info("Stable ID lookup source: search hub")
        return get_search_hub_results(params)

    logger.info("Stable ID lookup source: fast-match")
    try:
        return get_fast_match_results(params)
    except Exception as error:
        logger.warning(f"Fast-match lookup failed; falling back to search hub: {error}")
        return get_search_hub_results(params)


def get_search_hub_results(params: SearchPayload):
    try:
        session = requests.Session()
        with session.post(
            url=ENSEMBL_SEARCH_HUB_API, json=params.model_dump()
        ) as response:
            response.raise_for_status()
            return response.json()
    except requests.exceptions.HTTPError as error:
        logger.error(f"HTTPError: {error}")
        return None
    except Exception as error:
        logger.exception(error)
        return None


def get_fast_match_results(params: SearchPayload):
    """Look up stable IDs in the local fast-match Redb index.

    The index is generated with keys for stable and unversioned stable IDs, and
    values in the ``genome_id|doc_type`` format. Multiple matching records are
    delimited by ``+``.
    """
    if fm_py is None:
        raise RuntimeError("fm_py is not installed")

    if not FAST_MATCH_DB_PATH:
        raise RuntimeError("FAST_MATCH_DB_PATH is not configured")

    raw_matches = fm_py.find_key(params.stable_id, FAST_MATCH_DB_PATH)
    if raw_matches is None:
        logger.info("Fast-match stable ID lookup result: 0 matches")
        return {"matches": []}

    # Unversioned IDs are unchanged; only conventional terminal numeric
    # version suffixes (for example, ``ENSG00000127720.3``) are removed.
    unversioned_stable_id = re.sub(r"\.\d+$", "", params.stable_id)
    matches = []
    seen_genome_ids = set()

    for raw_match in raw_matches.split("+"):
        try:
            genome_id, doc_type = raw_match.split("|", maxsplit=1)
        except ValueError as error:
            raise ValueError(
                f"Invalid fast-match value for stable ID '{params.stable_id}'"
            ) from error

        if not genome_id or not doc_type:
            raise ValueError(
                f"Invalid fast-match value for stable ID '{params.stable_id}'"
            )

        if params.type and doc_type != params.type:
            continue

        if genome_id not in seen_genome_ids:
            matches.append(
                {
                    "genome_id": genome_id,
                    "unversioned_stable_id": unversioned_stable_id,
                }
            )
            seen_genome_ids.add(genome_id)

    logger.info(f"Fast-match stable ID lookup result: {len(matches)} matches")
    return {"matches": matches}

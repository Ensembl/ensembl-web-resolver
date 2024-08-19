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
        except requests.exceptions.HTTPError as HTTPError:
            logger.error(f"HTTPError: {HTTPError}")
            return None
        except Exception as e:
            logger.exception(e)
            return None

    return metadata_results

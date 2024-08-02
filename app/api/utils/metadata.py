from loguru import logger
import requests
from api.models.resolver import SearchPayload
from core.config import ENSEMBL_URL

def get_metadata(genome_id: str):
    try:
        session = requests.Session()
        with session.get(url=f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/details") as response:
            response.raise_for_status()
            return response.json()
    except requests.exceptions.HTTPError as HTTPError:
        logger.error(f"HTTPError: {HTTPError}")
        return None
    except Exception as e:
        logger.exception(e)
        return None
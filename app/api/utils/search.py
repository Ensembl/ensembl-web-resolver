import requests
from loguru import logger
from api.models.resolver import SearchPayload
from core.config import ENSEMBL_SEARCH_HUB_API


def get_search_results(params: SearchPayload):
    try:
        session = requests.Session()
        with session.post(
            url=ENSEMBL_SEARCH_HUB_API, json=params.model_dump()
        ) as response:
            response.raise_for_status()
            return response.json()
    except requests.exceptions.HTTPError as HTTPError:
        logger.error(f"HTTPError: {HTTPError}")
        return None
    except Exception as e:
        logger.exception(e)
        return None

from fastapi import APIRouter, Request
from typing import Optional
from fastapi.responses import RedirectResponse
from loguru import logger
import requests, logging
from core.logging import InterceptHandler
from api.models.resolver import SearchPayload
from api.error_response import response_error_handler
from core.config import ENSEMBL_SEARCH_HUB_API, DEFAULT_APP, ENSEMBL_URL
import aiohttp

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()
@router.get("/{stable_id}", name="Resolver")
def resolve(request: Request, stable_id: str, type: Optional[str] = "gene", gca: Optional[str] = "", app: Optional[str] = DEFAULT_APP):
  params = SearchPayload(
    stable_id = stable_id,
    type = type
  )
  try:
    session = requests.Session()
    search_results = {}
    with session.post(url=ENSEMBL_SEARCH_HUB_API,json=params.dict()) as response:
      response.raise_for_status()
      search_results = response.json()
  
  except requests.exceptions.HTTPError as HTTPError:
    return response_error_handler({"status": HTTPError.response.status_code})

  except Exception as e:
    logger.exception(e)
    return response_error_handler({"status": 500})

  if request.headers.get("content-type") == "application/json":
    return search_results
  else:
    matches = search_results.get("matches")
    if not matches:
      return {"response": "No matches found"}

    genome_id = matches[0].get("genome_id")

    url=f"{ENSEMBL_URL}/{app}/{genome_id}/{type}:{stable_id}"

    return RedirectResponse(url)

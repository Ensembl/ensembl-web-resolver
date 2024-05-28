from fastapi import APIRouter, Request
from typing import Optional
from fastapi.responses import RedirectResponse
from loguru import logger
import requests, logging
from core.logging import InterceptHandler
from api.models.resolver import SearchPayload
from api.error_response import response_error_handler
from core.config import ENSEMBL_SEARCH_HUB_API, DEFAULT_APP, ENSEMBL_URL

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()
@router.get("/{stable_id}/", name="Resolver")
async def resolve(request: Request, stable_id: str, type: Optional[str] = "gene", gca: Optional[str] = "", app: Optional[str] = DEFAULT_APP):
  params = SearchPayload(
    stable_id = stable_id,
    type = type
  )
  try:
    response = requests.post(ENSEMBL_SEARCH_HUB_API, json=params.dict())
  except Exception as e:
    logger.exception(e)
    return response_error_handler({"status": 500})


  if request.headers.get("content-type") == "application/json":
    return response.json()
  else:
    matches = response.json().get("matches")
    if not matches:
      return {"response": "No matches found"}

    genome_id = matches[0].get("genome_id")

    url=f"{ENSEMBL_URL}/{app}/{genome_id}/{type}:{stable_id}"

    return RedirectResponse(url)

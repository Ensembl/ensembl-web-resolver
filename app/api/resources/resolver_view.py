import os
from fastapi import APIRouter, Request
from typing import Optional
from fastapi.responses import RedirectResponse, HTMLResponse
from loguru import logger
import requests, logging
import aiohttp
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from core.logging import InterceptHandler
from api.models.resolver import SearchPayload
from api.error_response import response_error_handler
from core.config import ENSEMBL_SEARCH_HUB_API, DEFAULT_APP, ENSEMBL_URL

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()
@router.get("/{stable_id}", name="Resolver")
def resolve(request: Request, stable_id: str, type: Optional[str] = "gene", gca: Optional[str] = "", app: Optional[str] = DEFAULT_APP):

  params = SearchPayload(
    stable_id = stable_id,
    type = type,
    per_page = 10
  )

  # Get genome_ids from search api
  try:
    session = requests.Session()
    with session.post(url=ENSEMBL_SEARCH_HUB_API,json=params.dict()) as response:
      response.raise_for_status()
      search_results = response.json()
  except requests.exceptions.HTTPError as HTTPError:
    return response_error_handler({"status": HTTPError.response.status_code})

  except Exception as e:
    logger.exception(e)
    return response_error_handler({"status": 500})
  else:
    matches = search_results.get("matches")

  if not matches:
    return response_error_handler({"status": 404})

  # Get metadata for each genome
  results = []
  for match in matches:
    genome_id = match.get("genome_id")
    try:
      with session.get(url=f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/details") as response:
        response.raise_for_status()
    except requests.exceptions.HTTPError as HTTPError:
      return response_error_handler({"status": HTTPError.response.status_code})
    except Exception as e:
      logger.exception(e)
      return response_error_handler({"status": 500})
    else:
      meta_results = response.json()

      if not meta_results:
        return response_error_handler({"status": 404})

      if app == "entity-viewer":
        url = f"{ENSEMBL_URL}/{app}/{genome_id}/{type}:{stable_id}"
      else:
        url = f"{ENSEMBL_URL}/{app}/{genome_id}?focus={type}:{stable_id}"

      meta = {
        "accession_id": meta_results["assembly"]["accession_id"],
        "assembly_name": meta_results["assembly"]["name"],
        "species": meta_results["scientific_name"] if meta_results["scientific_name"] else meta_results["common_name"],
        "type": meta_results["type"],
        "resolved_url": url
      }

      results.append(meta)

  # return request.headers

  if "application/json" in request.headers.get("accept"):
    return results

  if len(results) == 1:
    return RedirectResponse(results[0]["resolved_url"])
  else:
    return HTMLResponse(generate_html_content(results))

def generate_html_content(results):
    # Create a simple HTML page with a list of URLs
  load_dotenv()
  CURR_DIR = os.path.dirname(os.path.abspath(__file__))
  env = Environment(loader=FileSystemLoader(os.path.join(CURR_DIR,"templates")))
  search_results_template = env.get_template("search_results.html")
  search_results_html = search_results_template.render(results = results)
  return search_results_html

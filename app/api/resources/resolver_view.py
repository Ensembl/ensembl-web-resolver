from fastapi import APIRouter, Request
from typing import Optional
from fastapi.responses import RedirectResponse, HTMLResponse
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
    type = type,
    per_page = 10
  )

  # Get genome_ids from search api
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
  else:
    matches = search_results.get("matches")

  if not matches:
    return response_error_handler({"status": 404})

  # Get assembly information
  meta_session = requests.Session()
  meta_results = {}
  resolved_genome_info = []

  for match in matches:
    genome_id = match.get("genome_id")
    try:
      with meta_session.get(url=f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/details") as meta_response:
        meta_response.raise_for_status()
    except requests.exceptions.HTTPError as HTTPError:
      return response_error_handler({"status": HTTPError.response.status_code})
    except Exception as e:
      logger.exception(e)
      return response_error_handler({"status": 500})
    else:
      meta_results = meta_response.json()

      if not meta_results:
        return response_error_handler({"status": 404})

      if app == "entity-viewer":
        url = f"{ENSEMBL_URL}/{app}/{genome_id}/{type}:{stable_id}"
      else:
        url = f"{ENSEMBL_URL}/{app}/{genome_id}?focus={type}:{stable_id}"

      meta = {
        "accession_id": meta_results["assembly"]["accession_id"],
        "assembly_name": meta_results["assembly"]["name"],
        "species_scientific_name": meta_results["scientific_name"],
        "taxonomy_id": meta_results["taxonomy_id"],
        "resolved_url": url
      }

      resolved_genome_info.append(meta)
    
  if request.headers.get("content-type") == "application/json":
    return resolved_genome_info

  if len(resolved_genome_info) == 1:
    return RedirectResponse(resolved_genome_info[0]["resolved_url"])
  else:
    return HTMLResponse(generate_html_content(resolved_genome_info))

def generate_html_content(resolved_genome_info):
    # Create a simple HTML page with a list of URLs
  html_content = "<html><body><h1>Resolved URLs</h1><table border='1' style='border-collapse: collapse;'><tr><th>Assembly Name</th><th>Accession ID</th><th>Ensembl URL</th></tr>"
  for genome_info in resolved_genome_info:
      html_content += f'<tr><td>{genome_info["assembly_name"]}</td><td>{genome_info["accession_id"]}</td><td><a href="{genome_info["resolved_url"]}">{genome_info["resolved_url"]}</a></td></tr>'
  html_content += "</table></body></html>"
  return html_content

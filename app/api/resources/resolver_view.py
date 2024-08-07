import os
from fastapi import APIRouter, Request
from typing import Optional, List
from fastapi.responses import RedirectResponse, HTMLResponse
import logging
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from core.logging import InterceptHandler
from api.models.resolver import SearchPayload, MetadataResult
from api.error_response import response_error_handler
from core.config import DEFAULT_APP, ENSEMBL_URL
from api.utils.metadata import get_metadata
from api.utils.search import get_search_results

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()
@router.get("/{stable_id}", name="Resolver")
async def resolve(request: Request, stable_id: str, type: Optional[str] = "gene", gca: Optional[str] = "", app: Optional[str] = DEFAULT_APP):

  params = SearchPayload(
    stable_id = stable_id,
    type = type,
    per_page = 10
  )

  # Get genome_ids from search api
  search_results = get_search_results(params)
  if not search_results:
      return response_error_handler({"status": 404})

  matches = search_results.get("matches")
  if not matches:
      return response_error_handler({"status": 404})

  # Get metadata for each genome
  results: List[MetadataResult] = []

  for match in matches:
    genome_id = match.get("genome_id")
    meta_result = get_metadata(genome_id)
    if not meta_result:
      continue

    if app == "entity-viewer":
      url = f"{ENSEMBL_URL}/{app}/{genome_id}/{type}:{stable_id}"
    else:
      url = f"{ENSEMBL_URL}/{app}/{genome_id}?focus={type}:{stable_id}"

    meta_result["resolved_url"] = url
    meta = MetadataResult(**meta_result)
    results.append(meta)

  if "application/json" in request.headers.get("accept"):
    return results

  if len(results) == 1:
    return RedirectResponse(results[0].resolved_url)
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

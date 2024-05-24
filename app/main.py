from fastapi import FastAPI, Request
from typing import Optional
from models.resolver import SearchPayload
from fastapi.responses import RedirectResponse
import requests, logging

app = FastAPI()

DEFAULT_APP = "entity-viewer"
ENSEMBL_URL = "http://beta.ensembl.org"
ENSEMBL_SEARCH_HUB_API = "http://0.0.0.0:8083/search_stable_id"
                           
@app.get("/id/{stable_id}/", name="Resolver")
async def resolve(request: Request, stable_id: str, type: Optional[str] = "gene", gca: Optional[str] = "", app: Optional[str] = DEFAULT_APP):
  params = SearchPayload(
    stable_id = stable_id,
    type = type
  )
  response = requests.post(ENSEMBL_SEARCH_HUB_API, json=params.dict())

  if request.headers.get("content-type") == "application/json":
    return response.json()
  else:
    matches = response.json().get("matches")
    if not matches:
      return {"response": "No matches found"}

    genome_id = matches[0].get("genome_id")

    url=f"{ENSEMBL_URL}/{app}/{genome_id}/{type}:{stable_id}"

    return RedirectResponse(url)

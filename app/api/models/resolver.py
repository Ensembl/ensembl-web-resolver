from typing import Optional, Literal, List
from pydantic import BaseModel, validator, Field


class SearchPayload(BaseModel):
  stable_id: str = Field(default = None, title = "Stable ID of a gene")
  type: Optional[Literal['gene']] = Field(default = None, title = "Type of stable id, e.g. gene" )
  per_page: int = 1
  # gca: Optional[str] = Field (default = None, title = "GCA accession id for the genome")
  # app: Optional[Literal['genome_browser', 'entity_viewer']] = Field (default = "entity_viewer", title = "Preferred app to be redirected to")

class Assembly(BaseModel):
  name: str
  accession_id: str

class MetadataResult(BaseModel):
  assembly: Assembly
  scientific_name: str
  common_name: str
  type: str = None
  resolved_url: str

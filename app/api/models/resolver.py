from typing import Optional, Literal, List
from pydantic import BaseModel, Field


class SearchPayload(BaseModel):
    stable_id: str = Field(default=None, title="Stable ID of a gene")
    type: Optional[Literal["gene"]] = Field(
        default=None, title="Type of stable id, e.g. gene"
    )
    per_page: int = 1
    app: Optional[Literal["genome-browser", "entity-viewer"]] = Field(
        default="entity-viewer", title="Preferred app to be redirected to"
    )


class SearchMatch(BaseModel):
    genome: str


class SearchResult(BaseModel):
    matches: List[SearchMatch] = []


class Assembly(BaseModel):
    name: str
    accession_id: str


class MetadataResult(BaseModel):
    assembly: Assembly
    scientific_name: str
    common_name: str
    type: Optional[str] = None


class ResolvedPayload(MetadataResult):
    resolved_url: str

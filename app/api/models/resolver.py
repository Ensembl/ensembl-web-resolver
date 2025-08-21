from enum import Enum
from typing import Optional, Literal, List, Dict, Annotated
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
    unversioned_stable_id: str


class SearchResult(BaseModel):
    matches: List[SearchMatch] = []


class Assembly(BaseModel):
    name: str
    accession_id: str


class MetadataResult(BaseModel):
    assembly: Assembly
    scientific_name: str
    common_name: str
    type: Optional[Dict[str, str]] = None
    is_reference: bool = False


class ResolvedPayload(MetadataResult):
    resolved_url: str


class RapidRedirectResponseType(str, Enum):
    HOME = "HOME"
    ERROR = "ERROR"
    BLAST = "BLAST"
    HELP = "HELP"
    INFO = "INFO"


class ResolvedURLResponse(BaseModel):
    response_type: Annotated[Optional[RapidRedirectResponseType], Field(exclude=True)] = None
    code: Annotated[Optional[int], Field(exclude=True)] = None
    resolved_url: str
    species_name: Annotated[Optional[str], Field(exclude=True)] = None
    gene_id: Annotated[Optional[str], Field(exclude=True)] = None
    location: Annotated[Optional[str], Field(exclude=True)] = None
    message: Annotated[Optional[str], Field(exclude=True)] = None

    class Config:
        use_enum_values = True

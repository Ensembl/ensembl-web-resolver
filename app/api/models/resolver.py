from enum import Enum
from typing import Optional, Literal, List, Dict, Annotated
from pydantic import BaseModel, Field, ConfigDict


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
    assembly: Optional[Assembly] = None
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    type: Optional[Dict[str, str]] = None
    is_reference: Optional[bool] = False


class ResolvedPayload(MetadataResult):
    resolved_url: str


class RapidResolverHtmlResponseType(str, Enum):
    HOME = "HOME"
    ERROR = "ERROR"
    BLAST = "BLAST"
    HELP = "HELP"
    INFO = "INFO"


class RapidResolverResponse(BaseModel):
    resolved_url: str
    response_type: Optional[RapidResolverHtmlResponseType] = None
    code: Optional[int] = None
    species_name: Optional[str] = None
    gene_id: Optional[str] = None
    location: Optional[str] = None
    message: Optional[str] = None
    rapid_archive_url: Optional[str] = None

    class Config:
        use_enum_values = True

    _excluded_fields = {
        "response_type", "code", "species_name", "gene_id",
        "location", "message", "rapid_archive_url"
    }

    def model_dump(self, *args, **kwargs):
        kwargs.setdefault("exclude", self._excluded_fields)
        return super().model_dump(*args, **kwargs)

    def model_dump_json(self, *args, **kwargs):
        kwargs.setdefault("exclude", self._excluded_fields)
        return super().model_dump_json(*args, **kwargs)


class StableIdResolverContent(MetadataResult):
    entity_viewer_url: Optional[str] = None
    genome_browser_url: Optional[str] = None

class StableIdResolverResponse(BaseModel):
    stable_id: str
    code: Optional[int] = None
    message: Optional[str] = None
    rapid_archive_url: Optional[str] = None
    content: Optional[List[StableIdResolverContent]] = []

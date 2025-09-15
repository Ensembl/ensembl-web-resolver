from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class SearchPayload(BaseModel):
    stable_id: str = Field(default=None, title="Stable ID of a gene")
    type: Literal["gene"] | None = Field(
        default=None, title="Type of stable id, e.g. gene"
    )
    per_page: int = 1
    app: Literal["genome-browser", "entity-viewer"] = Field(
        default="entity-viewer", title="Preferred app to be redirected to"
    )


class SearchMatch(BaseModel):
    genome: str
    unversioned_stable_id: str


class SearchResult(BaseModel):
    matches: list[SearchMatch]


class Assembly(BaseModel):
    name: str
    accession_id: str


class MetadataResult(BaseModel):
    assembly: Assembly | None = None
    scientific_name: str | None = None
    common_name: str | None = None
    type: dict[str, str] | None = None
    is_reference: bool = False


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
    response_type: RapidResolverHtmlResponseType | None = None
    code: int | None = None
    species_name: str | None = None
    gene_id: str | None = None
    location: str | None = None
    message: str | None = None
    rapid_archive_url: str | None = None

    model_config = ConfigDict(use_enum_values=True)

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
    entity_viewer_url: str | None = None
    genome_browser_url: str | None = None


class StableIdResolverResponse(BaseModel):
    stable_id: str
    code: int | None = None
    message: str | None = None
    rapid_archive_url: str | None = None
    content: list[StableIdResolverContent] | None = None

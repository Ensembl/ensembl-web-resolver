import logging

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.api.error_response import response_error_handler
from app.api.metrics import record_legacy_url_resolver_outcome
from app.api.models.resolver import UrlResolverResponse
from app.api.utils.commons import is_json_request
from app.api.utils.metadata import (
    MetadataNotFoundError,
    get_genome_tag_from_genome_id,
    search_variant,
)
from app.api.utils.species_mapping import (
    SpeciesMappingNotFoundError,
    SpeciesMappingConfigurationError,
    SpeciesNotFoundError,
    get_genome_uuid_from_species_url,
)
from app.api.utils.legacy_url_resolver import (
    InvalidLegacyUrlError,
    LegacyUrlResolverError,
    MissingUrlParameterError,
    UnsupportedLegacyUrlError,
    build_archive_fallback_url,
    is_bare_legacy_path,
    resolve_legacy_ensembl_url,
)
from app.api.utils.legacy_url_mapping import get_static_legacy_url_mapping
from app.core.logging import InterceptHandler

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()


@router.get("", name="Resolve legacy Ensembl URL")
async def resolve_url(request: Request, url: str):
    """Resolve a supported legacy Ensembl URL to its new Ensembl equivalent.

    Args:
        request: Incoming FastAPI request used to decide JSON vs redirect.
        url: Full legacy URL or path to resolve.

    Returns:
        JSON containing ``resolved_url`` when the client requests JSON, otherwise
        a redirect response to the resolved new Ensembl URL.
    """
    response_mode = "json" if is_json_request(request) else "html"

    try:
        resolved_url = resolve_legacy_ensembl_url(
            url,
            get_genome_uuid_from_species_url,
            get_genome_tag_from_genome_id,
            search_variant,
            get_static_legacy_url_mapping,
        )
        response = UrlResolverResponse(resolved_url=resolved_url)

        if response_mode == "json":
            record_legacy_url_resolver_outcome("resolved", response_mode)
            return response.model_dump(exclude_none=True)

        record_legacy_url_resolver_outcome("resolved", response_mode)
        return RedirectResponse(resolved_url, status_code=308)
    except MissingUrlParameterError as error:
        record_legacy_url_resolver_outcome("invalid_request", response_mode)
        return response_error_handler({"status": 400, "details": str(error)})
    except SpeciesMappingNotFoundError:
        if is_bare_legacy_path(url):
            if response_mode == "html":
                return _archive_fallback_response(url, response_mode)
            record_legacy_url_resolver_outcome("not_found", response_mode)
            return response_error_handler(
                {
                    "status": 404,
                    "details": "No supported new Ensembl equivalent for this URL",
                }
            )
        return _archive_fallback_response(url, response_mode)
    except SpeciesNotFoundError:
        # Archive fallback is an HTTP policy for unresolved species mappings.
        # The new Ensembl URL resolver stays focused on supported new Ensembl
        # destinations.
        return _archive_fallback_response(url, response_mode)
    except InvalidLegacyUrlError as error:
        record_legacy_url_resolver_outcome("not_found", response_mode)
        return response_error_handler({"status": 404, "details": str(error)})
    except UnsupportedLegacyUrlError as error:
        if response_mode == "html":
            return _archive_fallback_response(url, response_mode)

        record_legacy_url_resolver_outcome("not_found", response_mode)
        return response_error_handler({"status": 404, "details": str(error)})
    except MetadataNotFoundError as error:
        record_legacy_url_resolver_outcome("not_found", response_mode)
        return response_error_handler({"status": 404, "details": str(error)})
    except SpeciesMappingConfigurationError as error:
        logging.error(f"Species mapping configuration error: {error}")
        record_legacy_url_resolver_outcome("internal_error", response_mode)
        return response_error_handler({"status": 500, "details": str(error)})
    except LegacyUrlResolverError as error:
        record_legacy_url_resolver_outcome("invalid_request", response_mode)
        return response_error_handler({"status": 400, "details": str(error)})
    except Exception as error:
        logging.error(f"Error resolving legacy URL: {error}")
        record_legacy_url_resolver_outcome("internal_error", response_mode)
        return response_error_handler({"status": 500, "details": str(error)})


def _archive_fallback_response(url: str, response_mode: str):
    """Redirect to the archive equivalent for unresolved species mappings.

    Args:
        url: Legacy URL submitted by the caller.

    Returns:
        Redirect response to the archive URL, or a JSON error if no archive URL
        can be constructed.
    """
    try:
        archive_url = build_archive_fallback_url(url)
        record_legacy_url_resolver_outcome("archive_fallback", response_mode)
        return RedirectResponse(archive_url, status_code=308)
    except UnsupportedLegacyUrlError as error:
        record_legacy_url_resolver_outcome("not_found", response_mode)
        return response_error_handler({"status": 404, "details": str(error)})
    except InvalidLegacyUrlError as error:
        record_legacy_url_resolver_outcome("not_found", response_mode)
        return response_error_handler({"status": 404, "details": str(error)})

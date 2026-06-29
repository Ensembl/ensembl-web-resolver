import logging

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.api.error_response import response_error_handler
from app.api.models.resolver import UrlResolverResponse
from app.api.utils.commons import is_json_request
from app.api.utils.species_mapping import (
    SpeciesMappingConfigurationError,
    SpeciesNotFoundError,
    get_genome_uuid_from_species_url,
)
from app.api.utils.url_resolver import (
    InvalidLegacyUrlError,
    LegacyUrlResolverError,
    MissingUrlParameterError,
    UnsupportedLegacyUrlError,
    resolve_legacy_ensembl_url,
)
from app.core.logging import InterceptHandler

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()


@router.get("", name="Resolve legacy Ensembl URL")
async def resolve_url(request: Request, url: str):
    """Resolve a supported legacy Ensembl URL to its Beta equivalent.

    Args:
        request: Incoming FastAPI request used to decide JSON vs redirect.
        url: Full legacy URL or path to resolve.

    Returns:
        JSON containing ``resolved_url`` when the client requests JSON, otherwise
        a redirect response to the resolved Beta URL.
    """
    try:
        resolved_url = resolve_legacy_ensembl_url(url, get_genome_uuid_from_species_url)
        response = UrlResolverResponse(resolved_url=resolved_url)

        if is_json_request(request):
            return response.model_dump()

        return RedirectResponse(resolved_url, status_code=308)
    except MissingUrlParameterError as error:
        return response_error_handler({"status": 400, "details": str(error)})
    except (InvalidLegacyUrlError, SpeciesNotFoundError) as error:
        return response_error_handler({"status": 404, "details": str(error)})
    except UnsupportedLegacyUrlError as error:
        return response_error_handler({"status": 501, "details": str(error)})
    except SpeciesMappingConfigurationError as error:
        logging.error(f"Species mapping configuration error: {error}")
        return response_error_handler({"status": 500, "details": str(error)})
    except LegacyUrlResolverError as error:
        return response_error_handler({"status": 400, "details": str(error)})
    except Exception as error:
        logging.error(f"Error resolving legacy URL: {error}")
        return response_error_handler({"status": 500, "details": str(error)})

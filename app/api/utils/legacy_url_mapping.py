from functools import lru_cache
from urllib.parse import urlparse

from app.api.utils.species_mapping import SpeciesMappingConfigurationError
from app.core.config import SPECIES_MAPPING_DB_PATH


def _parse_legacy_url_for_static_mapping(legacy_url: str):
    """Parse a legacy URL for static host and path mapping lookup.

    Args:
        legacy_url: Full legacy URL, bare host, or path submitted by the caller.

    Returns:
        A parsed URL object suitable for static mapping normalization.

    Business rules:
        Scheme-less values whose first segment contains a dot are treated as
        hosts, e.g. ``staging-plants.ensembl.org``. Species paths without a
        scheme, e.g. ``Homo_sapiens/Gene/Summary``, remain path-only inputs.
    """
    if "://" in legacy_url or legacy_url.startswith("/"):
        return urlparse(legacy_url)

    first_segment = legacy_url.split("/", 1)[0]
    if "." in first_segment:
        return urlparse(f"//{legacy_url}")

    return urlparse(legacy_url)


def _normalise_static_path(path: str) -> str:
    """Normalize a legacy path for exact static path mapping.

    Args:
        path: Raw URL path from the submitted legacy URL.

    Returns:
        Lowercase path with one leading slash and no trailing slash, except for
        the root path.

    Business rules:
        Static path mappings ignore host, query string, and fragment. Matching
        is exact after case and trailing-slash normalization.
    """
    normalised_path = f"/{path.strip('/')}".lower()
    return "/" if normalised_path == "/" else normalised_path.rstrip("/")


def _normalise_static_host(host: str | None) -> str | None:
    """Normalize a legacy host for exact static host mapping.

    Args:
        host: Parsed URL hostname, or ``None`` for path-only submissions.

    Returns:
        Lowercase hostname, or ``None`` when no host was supplied.
    """
    return host.lower() if host else None


@lru_cache(maxsize=4096)
def get_static_legacy_url_mapping(legacy_url: str) -> str | None:
    """Fetch a static new Ensembl URL for a legacy host or path.

    Args:
        legacy_url: Full legacy URL, bare host, or path submitted by the caller.

    Returns:
        The configured target URL, or ``None`` when no static mapping matches.

    Raises:
        SpeciesMappingConfigurationError: If the shared DuckDB file path is not
            configured.

    Business rules:
        Host mappings are checked first and only apply to homepage requests.
        Path mappings are checked second and ignore the submitted host. Query
        strings and fragments are intentionally discarded; the returned URL is
        exactly the value stored in DuckDB.
    """
    if not SPECIES_MAPPING_DB_PATH:
        raise SpeciesMappingConfigurationError("SPECIES_MAPPING_DB_PATH is not set")

    parsed_url = _parse_legacy_url_for_static_mapping(legacy_url)
    source_host = _normalise_static_host(parsed_url.hostname)
    source_path = _normalise_static_path(parsed_url.path)

    # Import lazily to match species mapping behavior and keep tests that mock
    # this lookup independent from the DuckDB package.
    import duckdb

    with duckdb.connect(SPECIES_MAPPING_DB_PATH, read_only=True) as connection:
        if source_host and source_path == "/":
            result = connection.execute(
                """
                    SELECT target_url
                    FROM legacy_url_host_mappings
                    WHERE source_host = ?
                      AND enabled = TRUE
                    LIMIT 1
                """,
                [source_host],
            ).fetchone()

            if result:
                return result[0]

        result = connection.execute(
            """
                SELECT target_url
                FROM legacy_url_path_mappings
                WHERE source_path = ?
                  AND enabled = TRUE
                LIMIT 1
            """,
            [source_path],
        ).fetchone()

    return result[0] if result else None

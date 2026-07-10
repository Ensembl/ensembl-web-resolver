from dataclasses import dataclass
from typing import Callable
from urllib.parse import parse_qsl, quote, urlparse, urlunparse

from app.core.config import ENSEMBL_URL


class LegacyUrlResolverError(Exception):
    """Base class for legacy URL resolver failures."""


class InvalidLegacyUrlError(LegacyUrlResolverError):
    """Raised when the supplied URL cannot be parsed as an Ensembl URL."""


class MissingUrlParameterError(LegacyUrlResolverError):
    """Raised when a supported URL shape is missing a required query parameter."""


class UnsupportedLegacyUrlError(LegacyUrlResolverError):
    """Raised when the URL shape has no supported new Ensembl equivalent."""


ARCHIVE_HOSTS = {
    "www.ensembl.org": "jun2026.archive.ensembl.org",
    "plants.ensembl.org": "eg63-plants.ensembl.org",
    "metazoa.ensembl.org": "eg63-metazoa.ensembl.org",
    "fungi.ensembl.org": "eg63-fungi.ensembl.org",
    "protists.ensembl.org": "eg63-protists.ensembl.org",
    "bacteria.ensembl.org": "eg63-bacteria.ensembl.org",
}


@dataclass(frozen=True)
class LegacyUrlRule:
    """Rule that maps one legacy path shape to one new Ensembl URL shape."""

    path: tuple[str, ...]
    required_query_params: tuple[str, ...]
    build_url: Callable[[str, dict[str, list[str]]], str]


def _first_query_value(query_params: dict[str, list[str]], key: str) -> str | None:
    """Return the first non-empty value for a query parameter.

    Args:
        query_params: Parsed query parameter mapping.
        key: Query parameter name to inspect.

    Returns:
        The first value for ``key`` or ``None`` when absent/empty.
    """
    values = query_params.get(key) or []
    return values[0] if values and values[0] else None


def _require_query_value(query_params: dict[str, list[str]], key: str) -> str:
    """Return a required query value or raise a resolver error.

    Args:
        query_params: Parsed query parameter mapping.
        key: Required query parameter name.

    Returns:
        The first non-empty value for ``key``.

    Raises:
        MissingUrlParameterError: If the parameter is absent or empty.
    """
    value = _first_query_value(query_params, key)
    if not value:
        raise MissingUrlParameterError(f"Missing required query parameter '{key}'")
    return value


def _quote_url_part(value) -> str:
    """Quote a URL path or query component after normalizing to text.

    Args:
        value: Value to quote for use in a generated URL.

    Returns:
        Percent-encoded text safe for URL interpolation.
    """
    return quote(str(value), safe="")


def _build_species_url(genome_uuid: str, query_params: dict[str, list[str]]) -> str:
    """Build a new Ensembl genome page URL.

    Args:
        genome_uuid: new Ensembl genome UUID from the species mapping table.
        query_params: Parsed legacy query parameters. Unused for this rule.

    Returns:
        The resolved new Ensembl genome page URL.
    """
    return f"{ENSEMBL_URL}/genome/{_quote_url_part(genome_uuid)}"


def _build_location_url(genome_uuid: str, query_params: dict[str, list[str]]) -> str:
    """Build a new Ensembl genome browser URL focused on a genomic location.

    Args:
        genome_uuid: new Ensembl genome UUID from the species mapping table.
        query_params: Parsed legacy query parameters containing ``r``.

    Returns:
        The resolved new Ensembl genome browser URL.
    """
    location = _require_query_value(query_params, "r")
    encoded_location = quote(location, safe=":-")
    return (
        f"{ENSEMBL_URL}/genome-browser/{_quote_url_part(genome_uuid)}"
        f"?focus=location:{encoded_location}&location={encoded_location}"
    )


def _build_gene_browser_url(
    genome_uuid: str, query_params: dict[str, list[str]]
) -> str:
    """Build a new Ensembl genome browser URL focused on a gene.

    Args:
        genome_uuid: new Ensembl genome UUID from the species mapping table.
        query_params: Parsed legacy query parameters containing ``g``.

    Returns:
        The resolved new Ensembl genome browser URL.
    """
    gene_id = _require_query_value(query_params, "g")
    return (
        f"{ENSEMBL_URL}/genome-browser/{_quote_url_part(genome_uuid)}"
        f"?focus=gene:{_quote_url_part(gene_id)}"
    )


def _build_gene_feature_explorer_url(
    genome_uuid: str, query_params: dict[str, list[str]]
) -> str:
    """Build a new Ensembl feature explorer URL for a gene.

    Args:
        genome_uuid: new Ensembl genome UUID from the species mapping table.
        query_params: Parsed legacy query parameters containing ``g``.

    Returns:
        The resolved new Ensembl feature explorer URL.
    """
    gene_id = _require_query_value(query_params, "g")
    return (
        f"{ENSEMBL_URL}/feature-explorer/{_quote_url_part(genome_uuid)}"
        f"/gene:{_quote_url_part(gene_id)}"
    )


def _build_gene_homology_url(
    genome_uuid: str, query_params: dict[str, list[str]]
) -> str:
    """Build a new Ensembl feature explorer URL with the homology view selected.

    Args:
        genome_uuid: new Ensembl genome UUID from the species mapping table.
        query_params: Parsed legacy query parameters containing ``g``.

    Returns:
        The resolved new Ensembl feature explorer homology URL.
    """
    return f"{_build_gene_feature_explorer_url(genome_uuid, query_params)}?view=homology"


def _build_transcript_feature_explorer_url(
    genome_uuid: str, query_params: dict[str, list[str]]
) -> str:
    """Build a new Ensembl feature explorer URL for a transcript.

    Args:
        genome_uuid: new Ensembl genome UUID from the species mapping table.
        query_params: Parsed legacy query parameters containing ``t``.

    Returns:
        The resolved new Ensembl feature explorer URL.
    """
    transcript_id = _require_query_value(query_params, "t")
    return (
        f"{ENSEMBL_URL}/feature-explorer/{_quote_url_part(genome_uuid)}"
        f"/transcript:{_quote_url_part(transcript_id)}"
    )


def _build_transcript_protein_url(
    genome_uuid: str, query_params: dict[str, list[str]]
) -> str:
    """Build a new Ensembl feature explorer URL with the protein view selected.

    Args:
        genome_uuid: new Ensembl genome UUID from the species mapping table.
        query_params: Parsed legacy query parameters containing ``t``.

    Returns:
        The resolved new Ensembl transcript URL with the protein view selected.
    """
    return (
        f"{_build_transcript_feature_explorer_url(genome_uuid, query_params)}"
        "?view=protein"
    )


# These rules intentionally cover only spreadsheet rows with a practical new
# Ensembl equivalent. Rows marked "No", "Maybe", or needing extra
# variant/regulatory lookup should fail explicitly rather than produce a
# misleading redirect.
SUPPORTED_SPECIES_RULES = (
    LegacyUrlRule(("Info", "Index"), (), _build_species_url),
    LegacyUrlRule(("Location", "Genome"), (), _build_species_url),
    LegacyUrlRule(("Location", "View"), ("r",), _build_location_url),
    LegacyUrlRule(("Location", "View"), ("g",), _build_gene_browser_url),
    LegacyUrlRule(("Gene", "Summary"), ("g",), _build_gene_feature_explorer_url),
    LegacyUrlRule(
        ("Transcript", "Summary"), ("t",), _build_transcript_feature_explorer_url
    ),
    LegacyUrlRule(
        ("Transcript", "ProteinSummary"), ("t",), _build_transcript_protein_url
    ),
    LegacyUrlRule(("Gene", "Compara_Ortholog"), ("g",), _build_gene_homology_url),
    LegacyUrlRule(("Gene", "Compara_Paralog"), ("g",), _build_gene_homology_url),
)


def _parse_query(query: str) -> dict[str, list[str]]:
    """Parse legacy Ensembl query strings.

    Args:
        query: Raw query string from the URL.

    Returns:
        A mapping from query parameter names to all supplied values.
    """
    # Legacy Ensembl URLs commonly separate query parameters with semicolons.
    # Normalizing to ampersands lets parse_qsl handle both separators.
    pairs = parse_qsl(query.replace(";", "&"), keep_blank_values=True)
    query_params: dict[str, list[str]] = {}
    for key, value in pairs:
        query_params.setdefault(key, []).append(value)
    return query_params


def _normalise_path(path: str) -> tuple[str, ...]:
    """Split a URL path into comparable path segments.

    Args:
        path: Parsed URL path.

    Returns:
        Non-empty URL path segments.
    """
    return tuple(segment for segment in path.strip("/").split("/") if segment)


def is_bare_legacy_path(legacy_url: str) -> bool:
    """Check whether a legacy URL has exactly one path segment.

    Args:
        legacy_url: Full legacy Ensembl URL submitted by the caller.

    Returns:
        ``True`` when the URL path is a single segment, for example
        ``/Crocodylus_porosus`` or ``/foo``.
    """
    parsed_url = urlparse(legacy_url)
    return len(_normalise_path(parsed_url.path)) == 1


def build_archive_fallback_url(legacy_url: str) -> str:
    """Build an archive fallback URL for an unresolved legacy species URL.

    Args:
        legacy_url: Full legacy Ensembl URL submitted by the caller.

    Returns:
        Archive URL with the original path, query string, and fragment preserved.

    Raises:
        InvalidLegacyUrlError: If the URL has no path.
        UnsupportedLegacyUrlError: If the source host has no archive mapping.
    """
    parsed_url = urlparse(legacy_url)
    path_segments = _normalise_path(parsed_url.path)

    if not path_segments:
        raise InvalidLegacyUrlError("URL path is empty")

    # Archive fallback is deliberately host allow-listed. Unknown hosts should
    # fail visibly rather than redirect users to a guessed archive destination.
    archive_host = ARCHIVE_HOSTS.get((parsed_url.hostname or "").lower())
    if archive_host is None:
        raise UnsupportedLegacyUrlError("No archive fallback configured for this URL")

    return urlunparse(
        (
            "https",
            archive_host,
            parsed_url.path,
            "",
            parsed_url.query,
            parsed_url.fragment,
        )
    )


def _find_species_rule(
    legacy_path: tuple[str, ...], query_params: dict[str, list[str]]
) -> LegacyUrlRule | None:
    """Find the first supported rule for a species-scoped legacy URL.

    Args:
        legacy_path: Path segments after the species segment.
        query_params: Parsed legacy query parameters.

    Returns:
        A matching URL rule, or ``None`` when no supported rule exists.

    Raises:
        MissingUrlParameterError: If the path is supported but required query
            parameters are absent.
    """
    missing_requirements: set[str] = set()

    for rule in SUPPORTED_SPECIES_RULES:
        if legacy_path != rule.path:
            continue

        # Location/View is ambiguous in the path alone, so required query
        # parameters are part of rule matching rather than only validation.
        missing = [
            key
            for key in rule.required_query_params
            if not _first_query_value(query_params, key)
        ]
        if not missing:
            return rule

        missing_requirements.update(missing)

    if missing_requirements:
        missing = ", ".join(f"'{key}'" for key in sorted(missing_requirements))
        raise MissingUrlParameterError(f"Missing required query parameter {missing}")

    return None


def resolve_legacy_ensembl_url(
    legacy_url: str,
    species_to_genome_uuid: Callable[[str], str],
    static_legacy_url_mapping: Callable[[str], str | None] | None = None,
) -> str:
    """Resolve a supported legacy Ensembl URL to its new Ensembl equivalent.

    Args:
        legacy_url: Full legacy URL or path submitted by the caller.
        species_to_genome_uuid: Function that maps legacy species URL names to
            new Ensembl genome UUIDs.
        static_legacy_url_mapping: Optional function that maps configured legacy
            hosts or paths directly to their new Ensembl URLs.

    Returns:
        The resolved new Ensembl URL.

    Raises:
        InvalidLegacyUrlError: If the URL cannot be parsed.
        MissingUrlParameterError: If a supported URL is missing required params.
        UnsupportedLegacyUrlError: If no supported mapping exists.

    Business rules:
        Static host/path mappings are checked before species-aware mappings.
        They represent explicit product decisions for legacy pages that do not
        follow the species-scoped URL shapes handled below.
    """
    if static_legacy_url_mapping is not None:
        mapped_url = static_legacy_url_mapping(legacy_url)
        if mapped_url:
            return mapped_url

    parsed_url = urlparse(legacy_url)
    path_segments = _normalise_path(parsed_url.path)
    query_params = _parse_query(parsed_url.query)

    if not path_segments:
        raise InvalidLegacyUrlError("URL path is empty")

    # The spreadsheet templates place <species> in the first path segment for
    # the supported mappings, e.g. /Homo_sapiens/Gene/Summary?g=...
    species_url = path_segments[0]
    legacy_path = path_segments[1:]

    if not legacy_path:
        genome_uuid = species_to_genome_uuid(species_url)
        return _build_species_url(genome_uuid, query_params)

    rule = _find_species_rule(legacy_path, query_params)

    if rule is None:
        raise UnsupportedLegacyUrlError(
            "No supported new Ensembl equivalent for this URL"
        )

    genome_uuid = species_to_genome_uuid(species_url)
    return rule.build_url(genome_uuid, query_params)

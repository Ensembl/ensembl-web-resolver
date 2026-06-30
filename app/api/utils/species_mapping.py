from functools import lru_cache
import re

from app.core.config import SPECIES_MAPPING_DB_PATH, SPECIES_MAPPING_TABLE


class SpeciesMappingConfigurationError(Exception):
    """Raised when species mapping storage is not configured correctly."""


class SpeciesNotFoundError(Exception):
    """Raised when a legacy species URL name has no mapped genome UUID."""


class SpeciesMappingNotFoundError(SpeciesNotFoundError):
    """Raised when a legacy species URL name is absent from the mapping table."""


class SpeciesGenomeUuidNotFoundError(SpeciesNotFoundError):
    """Raised when a legacy species URL name exists but has no genome UUID."""


def _validate_table_name(table_name: str) -> str:
    """Validate a configured DuckDB table name.

    Args:
        table_name: Candidate table name from configuration.

    Returns:
        The validated table name.

    Raises:
        SpeciesMappingConfigurationError: If the table name is empty or unsafe.
    """
    if not table_name or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
        raise SpeciesMappingConfigurationError("Invalid species mapping table name")
    return table_name


@lru_cache(maxsize=4096)
def get_genome_uuid_from_species_url(species_url: str) -> str:
    """Fetch the Beta genome UUID for a legacy species URL name.

    Args:
        species_url: Legacy species path segment, for example ``Homo_sapiens``.

    Returns:
        The Beta genome UUID mapped to the legacy species URL name.

    Raises:
        SpeciesMappingConfigurationError: If the DuckDB file path is missing.
        SpeciesNotFoundError: If no mapping exists for the species URL name.
    """
    if not SPECIES_MAPPING_DB_PATH:
        raise SpeciesMappingConfigurationError("SPECIES_MAPPING_DB_PATH is not set")

    # Import lazily so unit tests that mock this function do not require DuckDB.
    import duckdb

    table_name = _validate_table_name(SPECIES_MAPPING_TABLE)
    query = f"""
        SELECT genome_uuid
        FROM {table_name}
        WHERE species_url = ?
        LIMIT 1
    """

    with duckdb.connect(SPECIES_MAPPING_DB_PATH, read_only=True) as connection:
        result = connection.execute(query, [species_url]).fetchone()

    # No row means the legacy species URL is absent from the mapping table.
    if not result:
        raise SpeciesMappingNotFoundError(
            f"No genome UUID found for species '{species_url}'"
        )

    genome_uuid = result[0]

    # A row with a NULL genome_uuid means this species has no Beta mapping and
    # should be handled by the archive fallback path.
    if genome_uuid is None:
        raise SpeciesGenomeUuidNotFoundError(
            f"No genome UUID found for species '{species_url}'"
        )

    # DuckDB may return UUID columns as uuid.UUID objects. Normalize at the
    # storage boundary so URL construction only deals with plain strings.
    return str(genome_uuid)

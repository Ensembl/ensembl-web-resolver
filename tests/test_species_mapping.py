import unittest
from unittest.mock import Mock, patch

from app.api.utils.species_mapping import (
    SpeciesNotFoundError,
    get_genome_uuid_from_species_url,
)


class TestSpeciesMapping(unittest.TestCase):
    def tearDown(self):
        get_genome_uuid_from_species_url.cache_clear()

    @patch("duckdb.connect")
    def test_get_genome_uuid_treats_null_uuid_as_not_found(self, mock_connect):
        """Treat rows with NULL genome_uuid as missing mappings."""
        connection = Mock()
        connection.__enter__ = Mock(return_value=connection)
        connection.__exit__ = Mock(return_value=None)
        connection.execute.return_value.fetchone.return_value = (None,)
        mock_connect.return_value = connection

        with self.assertRaises(SpeciesNotFoundError):
            get_genome_uuid_from_species_url("Homo_sapiens")


if __name__ == "__main__":
    unittest.main()

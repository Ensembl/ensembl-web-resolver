import tempfile
import unittest

import duckdb

from app.api.utils import legacy_url_mapping
from app.api.utils.legacy_url_mapping import get_static_legacy_url_mapping


class TestLegacyUrlMapping(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = f"{self.temp_dir.name}/resolver_mappings.db"

        with duckdb.connect(self.db_path) as connection:
            connection.execute(
                """
                    CREATE TABLE legacy_url_path_mappings (
                      source_path TEXT PRIMARY KEY,
                      target_url TEXT NOT NULL,
                      enabled BOOLEAN DEFAULT TRUE
                    );

                    CREATE TABLE legacy_url_host_mappings (
                      source_host TEXT PRIMARY KEY,
                      target_url TEXT NOT NULL,
                      enabled BOOLEAN DEFAULT TRUE
                    );

                    INSERT INTO legacy_url_path_mappings
                    VALUES
                      (
                        '/multi/tools/blast',
                        'https://dev-2020.ensembl.org/tools/blast',
                        TRUE
                      ),
                      (
                        '/multi/search/results',
                        'https://dev-2020.ensembl.org/species-selector',
                        TRUE
                      );

                    INSERT INTO legacy_url_host_mappings
                    VALUES
                      (
                        'staging-protists.ensembl.org',
                        'https://dev-2020.ensembl.org',
                        TRUE
                      );
                """
            )

        self.original_db_path = legacy_url_mapping.SPECIES_MAPPING_DB_PATH
        legacy_url_mapping.SPECIES_MAPPING_DB_PATH = self.db_path
        get_static_legacy_url_mapping.cache_clear()

    def tearDown(self):
        legacy_url_mapping.SPECIES_MAPPING_DB_PATH = self.original_db_path
        get_static_legacy_url_mapping.cache_clear()
        self.temp_dir.cleanup()

    def test_get_static_mapping_ignores_host_for_path_mappings(self):
        """Map matching paths regardless of the submitted legacy host."""
        self.assertEqual(
            get_static_legacy_url_mapping(
                "https://staging-plants.ensembl.org/Multi/Tools/Blast"
            ),
            "https://dev-2020.ensembl.org/tools/blast",
        )
        self.assertEqual(
            get_static_legacy_url_mapping(
                "https://www.ensembl.org/Multi/Tools/Blast"
            ),
            "https://dev-2020.ensembl.org/tools/blast",
        )

    def test_get_static_mapping_normalizes_path_case_and_trailing_slash(self):
        """Treat case and a final slash as insignificant for exact path matches."""
        self.assertEqual(
            get_static_legacy_url_mapping(
                "https://www.ensembl.org/multi/tools/blast/"
            ),
            "https://dev-2020.ensembl.org/tools/blast",
        )

    def test_get_static_mapping_discards_query_string(self):
        """Return the stored target URL without preserving legacy query values."""
        self.assertEqual(
            get_static_legacy_url_mapping(
                "https://www.ensembl.org/Multi/Search/Results?q=brca2"
            ),
            "https://dev-2020.ensembl.org/species-selector",
        )

    def test_get_static_mapping_handles_bare_host_homepage(self):
        """Resolve configured scheme-less host homepages."""
        self.assertEqual(
            get_static_legacy_url_mapping("staging-protists.ensembl.org"),
            "https://dev-2020.ensembl.org",
        )

    def test_get_static_mapping_does_not_apply_host_mapping_to_paths(self):
        """Keep host mappings scoped to homepage requests only."""
        self.assertIsNone(
            get_static_legacy_url_mapping(
                "https://staging-protists.ensembl.org/Homo_sapiens"
            )
        )


if __name__ == "__main__":
    unittest.main()

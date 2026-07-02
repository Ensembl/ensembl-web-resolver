import unittest
from uuid import UUID
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.utils.species_mapping import (
    SpeciesGenomeUuidNotFoundError,
    SpeciesMappingNotFoundError,
    SpeciesNotFoundError,
)
from app.core.config import ENSEMBL_URL, STATIC_PATH
from app.main import app


class TestUrlResolver(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_url_resolver_api_url = "/legacy"
        self.genome_uuid = "genome_uuid1"

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_species_home_with_json_response(self, mock_species_lookup):
        """Resolve a species home URL to the new Ensembl species page."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Homo_sapiens/Info/Index"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"resolved_url": f"{ENSEMBL_URL}/species/{self.genome_uuid}"},
        )
        mock_species_lookup.assert_called_once_with("Homo_sapiens")

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_bare_species_path_with_redirect(self, mock_species_lookup):
        """Resolve a bare species path to the new Ensembl species page."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Crocodylus_porosus"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            f"{ENSEMBL_URL}/species/{self.genome_uuid}",
        )
        mock_species_lookup.assert_called_once_with("Crocodylus_porosus")

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_bare_species_path_without_uuid_redirects_to_archive(
        self, mock_species_lookup
    ):
        """Redirect bare species paths to archive when no new Ensembl UUID exists."""
        mock_species_lookup.side_effect = SpeciesGenomeUuidNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Homo_sapiens"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://jun2026.archive.ensembl.org/Homo_sapiens",
        )
        mock_species_lookup.assert_called_once_with("Homo_sapiens")

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_gene_summary_with_redirect(self, mock_species_lookup):
        """Resolve a supported gene URL to a permanent new Ensembl redirect."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Summary"
                    "?g=ENSG00000012048"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            (f"{ENSEMBL_URL}/entity-viewer/{self.genome_uuid}" "/gene:ENSG00000012048"),
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_gene_summary_with_uuid_lookup_value(self, mock_species_lookup):
        """Resolve URLs when DuckDB returns genome UUID as a UUID object."""
        genome_uuid = UUID("12345678-1234-5678-1234-567812345678")
        mock_species_lookup.return_value = genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Summary"
                    "?g=ENSG00000012048"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/entity-viewer/{genome_uuid}" "/gene:ENSG00000012048"
                )
            },
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_location_view_with_semicolon_query(self, mock_species_lookup):
        """Resolve old-style semicolon-delimited query strings."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Location/View"
                    "?db=core;r=17:38449840-38530994"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/genome-browser/{self.genome_uuid}"
                    "?focus=location:17:38449840-38530994"
                    "&location=17:38449840-38530994"
                )
            },
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_transcript_summary(self, mock_species_lookup):
        """Resolve a transcript summary URL to the new Ensembl entity viewer."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Transcript/Summary"
                    "?t=ENST00000357654"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/entity-viewer/{self.genome_uuid}"
                    "/transcript:ENST00000357654"
                )
            },
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_missing_required_query_parameter(self, mock_species_lookup):
        """Return 400 when a URL shape is known but its parameter is missing."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 400)

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_unsupported_template(self, mock_species_lookup):
        """Return 404 for spreadsheet rows with no supported new Ensembl mapping."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Expression"
                    "?g=ENSG00000012048"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        mock_species_lookup.assert_not_called()

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_missing_species_redirects_to_main_archive(
        self, mock_species_lookup
    ):
        """Redirect main-site URLs to the release archive when UUID is missing."""
        mock_species_lookup.side_effect = SpeciesGenomeUuidNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Homo_sapiens/Info/Index"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://jun2026.archive.ensembl.org/Homo_sapiens/Info/Index",
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_null_species_uuid_redirects_to_main_archive(
        self, mock_species_lookup
    ):
        """Redirect to archive when a species row has no new Ensembl genome UUID."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Summary"
                    "?g=ENSG00000012048"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://jun2026.archive.ensembl.org/Homo_sapiens/Gene/Summary"
            "?g=ENSG00000012048",
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_missing_species_redirects_to_plants_archive(
        self, mock_species_lookup
    ):
        """Redirect plants URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://plants.ensembl.org/Arabidopsis_thaliana/Info/Index"
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://eg63-plants.ensembl.org/Arabidopsis_thaliana/Info/Index",
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_missing_species_redirects_to_metazoa_archive(
        self, mock_species_lookup
    ):
        """Redirect metazoa URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://metazoa.ensembl.org/Caenorhabditis_elegans/Info/Index"
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://eg63-metazoa.ensembl.org/Caenorhabditis_elegans/Info/Index",
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_missing_species_redirects_to_fungi_archive(
        self, mock_species_lookup
    ):
        """Redirect fungi URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://fungi.ensembl.org/Saccharomyces_cerevisiae/Info/Index"
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://eg63-fungi.ensembl.org/Saccharomyces_cerevisiae/Info/Index",
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_missing_species_redirects_to_protists_archive(
        self, mock_species_lookup
    ):
        """Redirect protists URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://protists.ensembl.org/Plasmodium_falciparum/Info/Index"
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://eg63-protists.ensembl.org/Plasmodium_falciparum/Info/Index",
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_missing_species_redirects_to_bacteria_archive(
        self, mock_species_lookup
    ):
        """Redirect bacteria URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://bacteria.ensembl.org/"
                    "Aliiglaciecola_lipolytica_e3_gca_000314975/Info/Index"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            (
                "https://eg63-bacteria.ensembl.org/"
                "Aliiglaciecola_lipolytica_e3_gca_000314975/Info/Index"
            ),
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_missing_species_archive_preserves_query_and_fragment(
        self, mock_species_lookup
    ):
        """Preserve legacy URL query strings and fragments in archive fallback."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Location/View"
                    "?r=1:1-100#content"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://jun2026.archive.ensembl.org/Homo_sapiens/Location/View"
            "?r=1:1-100#content",
        )

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_missing_species_unknown_host_does_not_redirect(
        self, mock_species_lookup
    ):
        """Return an error for unknown hosts instead of guessing an archive URL."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://example.org/Homo_sapiens/Info/Index"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("location", response.headers)

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_unknown_page_with_json_response(self, mock_species_lookup):
        """Return JSON error for unsupported one-segment legacy paths."""
        mock_species_lookup.side_effect = SpeciesMappingNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/foo"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("location", response.headers)
        mock_species_lookup.assert_called_once_with("foo")

    @patch("app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_unknown_page_with_html_interstitial(self, mock_species_lookup):
        """Render a choice page for browser users on unsupported legacy paths."""
        mock_species_lookup.side_effect = SpeciesMappingNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/foo"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("location", response.headers)
        self.assertIn("This page could not be resolved", response.text)
        self.assertIn(f"{ENSEMBL_URL}/species-selector", response.text)
        self.assertIn("https://jun2026.archive.ensembl.org/foo", response.text)
        self.assertIn(f"{STATIC_PATH}/css/styles.css", response.text)
        mock_species_lookup.assert_called_once_with("foo")


if __name__ == "__main__":
    unittest.main()

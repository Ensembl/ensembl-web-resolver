import unittest
from uuid import UUID
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import ENSEMBL_URL
from app.main import app


class TestUrlResolver(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_url_resolver_api_url = "/resolve-url"
        self.genome_uuid = "genome_uuid1"

    @patch("app.api.resources.url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_species_home_with_json_response(self, mock_species_lookup):
        """Resolve a species home URL to the Beta species page."""
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

    @patch("app.api.resources.url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_gene_summary_with_redirect(self, mock_species_lookup):
        """Resolve a supported gene URL to a permanent Beta redirect."""
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

    @patch("app.api.resources.url_resolver_view.get_genome_uuid_from_species_url")
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

    @patch("app.api.resources.url_resolver_view.get_genome_uuid_from_species_url")
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

    @patch("app.api.resources.url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_transcript_summary(self, mock_species_lookup):
        """Resolve a transcript summary URL to the Beta entity viewer."""
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

    @patch("app.api.resources.url_resolver_view.get_genome_uuid_from_species_url")
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

    @patch("app.api.resources.url_resolver_view.get_genome_uuid_from_species_url")
    def test_resolve_unsupported_template(self, mock_species_lookup):
        """Return 501 for spreadsheet rows with no supported Beta mapping."""
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

        self.assertEqual(response.status_code, 501)


if __name__ == "__main__":
    unittest.main()

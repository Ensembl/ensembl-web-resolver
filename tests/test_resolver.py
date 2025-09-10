import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.core.config import ENSEMBL_URL, DEFAULT_APP
from app.main import app


class TestResolverAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.api_prefix = ""
        self.mock_search_api_url = "/id"
        self.stable_id = "ENSAROG00010015245"

        self.mock_single_search_results_success = {
            "matches": [
                {"genome_id": "genome1", "unversioned_stable_id": "ENSAROG00010015245"}
            ]
        }
        self.mock_single_metadata_results_success = {
            "genome1": {
                "assembly": {"accession_id": "GCA_018555375.2", "name": "ASM1855537v1.1"},
                "scientific_name": "Anguilla rostrata",
                "common_name": "American eel",
                "type": {"kind": "strain", "value": "reference"},
                "unversioned_stable_id": "ENSAROG00010015245",
            }
        }

        self.mock_multiple_search_results_success = {
            "matches": [
                {"genome_id": "genome1", "unversioned_stable_id": "ENSAROG00010015245"},
                {"genome_id": "genome2", "unversioned_stable_id": "ENSAROG00010015245"},
            ]
        }

        # Mock metadata API
        self.mock_multiple_metadata_results_success = {
            "genome1": {
                "assembly": {"accession_id": "GCA_018555375.2", "name": "ASM1855537v1.1"},
                "scientific_name": "Anguilla rostrata",
                "common_name": "American eel",
                "type": {"kind": "strain", "value": "reference"},
                "unversioned_stable_id": "ENSAROG00010015245",
            },
            "genome2": {
                "assembly": {"accession_id": "GCA_018555375.3", "name": "ASM1855537v3"},
                "scientific_name": "Anguilla rostrata",
                "common_name": "American eel",
                "type": {"kind": "strain", "value": "reference"},
                "unversioned_stable_id": "ENSAROG00010015245",
            },
        }

        self.mock_resolved_url = {
            "genome1": f"{ENSEMBL_URL}/{DEFAULT_APP}/genome1/gene:{self.stable_id}",
            "genome2": f"{ENSEMBL_URL}/{DEFAULT_APP}/genome2/gene:{self.stable_id}",
        }

    @patch("app.api.resources.resolver_view.get_search_results")
    @patch("app.api.resources.resolver_view.get_metadata")
    def test_resolve_success_with_json_response(
        self, mock_get_metadata, mock_get_search_results
    ):

        mock_get_search_results.return_value = self.mock_multiple_search_results_success
        mock_get_metadata.return_value = self.mock_multiple_metadata_results_success

        response = self.client.get(
            f"{self.mock_search_api_url}/{self.stable_id}",
            follow_redirects=False,
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response.headers["content-type"])

        json_response = response.json()
        self.assertEqual(len(json_response), 2)
        self.assertEqual(
            json_response[0]["entity_viewer_url"], self.mock_resolved_url["genome1"]
        )

    @patch("app.api.resources.resolver_view.get_search_results")
    @patch("app.api.resources.resolver_view.get_metadata")
    def test_resolve_success_with_redirect(
        self, mock_get_metadata, mock_get_search_results
    ):

        mock_get_search_results.return_value = self.mock_single_search_results_success
        mock_get_metadata.return_value = self.mock_single_metadata_results_success

        response = self.client.get(
            f"{self.mock_search_api_url}/{self.stable_id}", follow_redirects=False
        )

        self.assertEqual(response.status_code, 307)  # Temporary Redirect
        self.assertIn("location", response.headers)
        self.assertEqual(
            response.headers["location"], self.mock_resolved_url["genome1"]
        )

    @patch("app.api.resources.resolver_view.get_search_results")
    @patch("app.api.resources.resolver_view.get_metadata")
    def test_resolve_success_with_html_response(
        self, mock_get_metadata, mock_get_search_results
    ):

        mock_get_search_results.return_value = self.mock_multiple_search_results_success
        mock_get_metadata.return_value = self.mock_multiple_metadata_results_success

        response = self.client.get(
            f"{self.mock_search_api_url}/{self.stable_id}", follow_redirects=False
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.mock_resolved_url["genome1"],
            response.text,
            "Failed resolving multiple results with html response",
        )

    @patch("app.api.resources.resolver_view.get_search_results")
    def test_resolve_404(self, mock_get_search_results):

        mock_get_search_results.return_value = {}

        response = self.client.get(
            f"{self.mock_search_api_url}/{self.stable_id}", follow_redirects=False,
            headers = {"accept": "application/json"}
        )
        self.assertEqual(response.status_code, 404)

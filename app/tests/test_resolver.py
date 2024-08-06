from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

from api.resources.resolver_view import router, get_search_results, get_metadata, ENSEMBL_URL, DEFAULT_APP, generate_html_content, response_error_handler, SearchPayload


class TestResolver:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self.default_app = DEFAULT_APP
        self.stable_id = "ENSG0001"
        self.type = "gene"

        self.mocked_url = {
            "genome1": f"{ENSEMBL_URL}/{self.default_app}/genome1/{self.type}:{self.stable_id}",
            "genome2": f"{ENSEMBL_URL}/{self.default_app}/genome2/{self.type}:{self.stable_id}"
        }

        self.mock_search_results = {
            "matches": [
                {"genome_id": "genome1"},
                {"genome_id": "genome2"}
            ]
        }

        self.mock_metadata = {
            "genome1": {
                "assembly": {"accession_id": "GCA_000001405.28", "name": "GRCh38"},
                "scientific_name": "Homo sapiens",
                "common_name": "Human",
                "type": "Genome"
            },
            "genome2": {
                "assembly": {"accession_id": "GCA_000001635.9", "name": "GRCm38"},
                "scientific_name": "Mus musculus",
                "common_name": "Mouse",
                "type": "Genome"
            }
        }

    @pytest.fixture
    def mock_get_search_results(self):
        with patch('api.resources.resolver_view.get_search_results') as mock:
            mock.return_value = self.mock_search_results
            yield mock

    @pytest.fixture
    def mock_get_metadata(self):
        with patch('api.resources.resolver_view.get_metadata') as mock:
            def side_effect(genome_id):
                return self.mock_metadata.get(genome_id)
            mock.side_effect = side_effect
            yield mock

    def test_resolve_success_with_json_response(self, mock_get_search_results, mock_get_metadata):
        response = self.client.get(f"/{self.stable_id}", headers={"accept": "application/json"})

        assert response.status_code == 200
        assert response.json() == [
            {
                "assembly": {
                    "accession_id": "GCA_000001405.28",
                    "name": "GRCh38"
                },
                "scientific_name": "Homo sapiens",
                "common_name": "Human",
                "type": "Genome",
                "resolved_url": self.mocked_url.get("genome1")
            },
            {
                "assembly": {
                    "accession_id": "GCA_000001635.9",
                    "name": "GRCm38"
                },
                "scientific_name": "Mus musculus",
                "common_name": "Mouse",
                "type": "Genome",
                "resolved_url": self.mocked_url.get("genome2")
            }
        ]

    def test_resolve_success_with_redirect(self, mock_get_search_results, mock_get_metadata):

        mock_get_search_results.return_value = {
            "matches": [
                {"genome_id": "genome1"}
            ]
        }

        mock_get_metadata.return_value = self.mock_metadata.get("genome1")
        
        response = self.client.get(f"/{self.stable_id}", follow_redirects=False)

        assert response.status_code == 307
        assert response.headers["location"] == self.mocked_url.get("genome1")

    def test_resolve_success_with_html_response(self, mock_get_search_results, mock_get_metadata):

        response = self.client.get(f"/{self.stable_id}")

        assert response.status_code == 200
        assert self.mocked_url.get("genome1") in response.text

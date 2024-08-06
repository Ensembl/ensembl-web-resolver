from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

from api.resources.resolver_view import router, get_search_results, get_metadata, ENSEMBL_URL, DEFAULT_APP, generate_html_content, response_error_handler, SearchPayload


class TestResolverService:

    # Define the mock data as class attributes
    MOCK_SEARCH_RESULTS = {
        "matches": [
            {"genome_id": "genome1"},
            {"genome_id": "genome2"}
        ]
    }

    MOCK_METADATA = {
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

    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    @pytest.fixture
    def mock_get_search_results(self):
        with patch('api.resources.resolver_view.get_search_results') as mock:
            mock.return_value = self.MOCK_SEARCH_RESULTS
            yield mock

    @pytest.fixture
    def mock_get_metadata(self):
        with patch('api.resources.resolver_view.get_metadata') as mock:
            def side_effect(genome_id):
                return self.MOCK_METADATA.get(genome_id)
            mock.side_effect = side_effect
            yield mock

    def test_resolve_success_with_json_response(self, mock_get_search_results, mock_get_metadata):
        stable_id = "ENSG0001"
        type = "gene"
        app = "entity-viewer"

        response = self.client.get(f"/{stable_id}", headers={"accept": "application/json"})

        assert response.status_code == 200
        assert response.json() == [
            {
                "accession_id": "GCA_000001405.28",
                "assembly_name": "GRCh38",
                "scientific_name": "Homo sapiens",
                "common_name": "Human",
                "type": "Genome",
                "resolved_url": f"{ENSEMBL_URL}/{app}/genome1/{type}:{stable_id}"
            },
            {
                "accession_id": "GCA_000001635.9",
                "assembly_name": "GRCm38",
                "scientific_name": "Mus musculus",
                "common_name": "Mouse",
                "type": "Genome",
                "resolved_url": f"{ENSEMBL_URL}/{app}/genome2/{type}:{stable_id}"
            }
        ]

    def test_resolve_success_with_redirect(self, mock_get_search_results, mock_get_metadata):
        stable_id = "ENSG0001"
        type = "gene"
        app = DEFAULT_APP

        mock_get_search_results.return_value = {
            "matches": [
                {"genome_id": "genome1"}
            ]
        }

        mock_get_metadata.return_value = self.MOCK_METADATA.get("genome1")
        
        response = self.client.get(f"/{stable_id}", follow_redirects=False, headers={"accept": "text/html"})

        assert response.status_code == 307
        assert response.headers["location"] == f"{ENSEMBL_URL}/{app}/genome1/{type}:{stable_id}"

    def test_resolve_success_with_html_response(self, mock_get_search_results, mock_get_metadata):
        stable_id = "ENSG0001"
        type = "gene"
        app = DEFAULT_APP

        mock_generate_html_content = patch('api.resources.resolver_view.generate_html_content', return_value="<html>Mocked HTML</html>")

        with mock_generate_html_content as mock_html:
            response = self.client.get(f"/{stable_id}", headers={"accept": "text/html"})

            assert response.status_code == 200
            assert response.text == "<html>Mocked HTML</html>"


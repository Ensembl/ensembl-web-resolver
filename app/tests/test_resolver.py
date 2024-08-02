import unittest
from unittest.mock import patch, MagicMock, Mock
from fastapi.testclient import TestClient
from core.config import ENSEMBL_URL
from main import app
import requests
from fastapi import Request
import json
import api
from api.resources.resolver_view import resolve

class TestResolverAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.api_prefix = ""
        self.mock_search_api_url = "/id" 
        
        self.mock_search_results_success = {
            "matches": [
                {"genome_id": "genome1"},
                {"genome_id": "genome2"}
            ]
        }

    # @patch("api.utils.search.get_search_results")
    # def test_get_search_results_successful(self, mock_requests):
    #     # mock the response
    #     mock_response = MagicMock()
    #     mock_response.status_code = 200
    #     # Mock search API
    #     mock_search_results = {
    #         "matches": [
    #             {"genome_id": "genome1"},
    #             {"genome_id": "genome2"}
    #         ]
    #     }        
    #     mock_response.json.return_value = mock_search_results

    #     # specify the return value of the post() method
    #     mock_requests.post.return_value = mock_response

    #     self.assertEqual(mock_response.status_code, 200)
    #     self.assertEqual(len(mock_response.json().get("matches")), 2)

    # @patch("api.utils.metadata.get_metadata")
    # def test_get_metadata(self, mock_requests):
    #     # mock the response
    #     mock_response = MagicMock()
    #     mock_response.status_code = 200
    #     # Mock search API
    #     metadata_response = [
    #         {
    #             "assembly": {"accession_id": "GCA_000001405.28", "name": "GRCh38"},
    #             "scientific_name": "Homo sapiens",
    #             "common_name": "Human",
    #             "type": "genome"
    #         },
    #         {
    #             "assembly": {"accession_id": "GCA_000001405.14", "name": "GRCh37"},
    #             "scientific_name": "Homo sapiens",
    #             "common_name": "Human",
    #             "type": "genome"
    #         }
    #     ]     
    #     mock_response.json.return_value = metadata_response

    #     # specify the return value of the post() method
    #     mock_requests.get.return_value = mock_response

    #     self.assertEqual(mock_response.status_code, 200)



    # def conditional_mock(*args, **kwargs):
    #   # Check if the request method is GET
    #   if kwargs.get('method', 'GET') == 'GET':
    #     # Call the real function if it's a GET request
    #     return api.utils.search.get_search_results.original(*args, **kwargs)
    #   else:
    #     # Mock response for other methods
    #     mock_response = Mock()
    #     mock_response.json.return_value = {
    #         "matches": [
    #             {"genome_id": "genome1"},
    #             {"genome_id": "genome2"}
    #         ]
    #     }
    #     return mock_response


    @patch("api.utils.search.get_search_results")
    def test_resolve_success(self, mock_get_search_results):
        stable_id = "ENSG00000139618"
        type = "gene"
        app_name = "genome_browser"
        
        mock_get_search_results.return_value = self.mock_search_results_success

        response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False, headers={"Accept": "text/html"})
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.headers['content-type'])

        # json_response = response.json()
        # self.assertEqual(len(json_response), 2)

        # mock_get_search_results.assert_called_once_with('https://jsonplaceholder.typicode.com/albums/1')


    # def mock_get_search_results(self):
    #      return MagicMock()
    
    # @patch("api.utils.search.get_search_results", new=mock_get_search_results)
    # def xresolve_success(self):
    #     stable_id = "ENSG00000139618"
    #     type = "gene"
    #     app_name = "genome_browser"
        
    #     self.mock_get_search_results = self.mock_search_results_success
    #     response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False, headers={"Accept": "text/html"})
    #     self.assertEqual(response.status_code, 200)


    # @patch("api.utils.search.get_search_results")
    # @patch("api.utils.metadata.get_metadata")
    # def resolve_success(self, mock_get_search_results):
    #     stable_id = "ENSG00000139618"
    #     type = "gene"
    #     app_name = "genome_browser"

    #     # Mock search API
    #     mock_search_results_success = {
    #         "matches": [
    #             {"genome_id": "genome1"},
    #             {"genome_id": "genome2"}
    #         ]
    #     }


    #     # mock_get_search_results.assert_called_once_with("https://jsonplaceholder.typicode.com/albums/1")


    #     # # Mock metadata API
    #     # mock_post_response_success = [
    #     #     {
    #     #         "assembly": {"accession_id": "GCA_000001405.28", "name": "GRCh38"},
    #     #         "scientific_name": "Homo sapiens",
    #     #         "common_name": "Human",
    #     #         "type": "genome"
    #     #     },
    #     #     {
    #     #         "assembly": {"accession_id": "GCA_000001405.14", "name": "GRCh37"},
    #     #         "scientific_name": "Homo sapiens",
    #     #         "common_name": "Human",
    #     #         "type": "genome"
    #     #     }
    #     # ]


    #     # mock_get_metadata.return_value = MagicMock(json.dumps(mock_post_response_success))

    #     # request: Request, stable_id: str, type: Optional[str] = "gene", gca: Optional[str] = "", app: Optional[str] = DEFAULT_APP)
    #     # Use TestClient to create a base request
    #     base_request = self.client.build_request("GET", f"{self.mock_search_api_url}/{stable_id}")

    #     # Create the new request with the required path parameters
    #     req = Request(base_request.scope, receive=base_request.receive)

    #     # req = Request
    #     # req.path_params = f"{self.mock_search_api_url}/{stable_id}"
    #     response = resolve(req, stable_id)

        # mock_get_search_results.return_value = mock_search_results_success
        # mock_get_search_results.side_effect = self.conditional_mock


        # response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False, headers={"Accept": "text/html"},)


        # Assertions
        # self.assertEqual(response.status_code, 200)
        # mock_get_search_results.assert_called_once()

        # self.assertIn('application/json', response.headers['content-type'])

        # json_response = response.json()
        # self.assertEqual(len(json_response), 2)
        # self.assertEqual(json_response[0]['accession_id'], "GCA_000001405.28")
        # self.assertEqual(json_response[0]['assembly_name'], "GRCh38")
        # self.assertEqual(json_response[0]['scientific_name'], "Homo_sapiens")
        # self.assertEqual(json_response[0]['common_name'], "Human")
        # self.assertEqual(json_response[0]['type'], "genome")
        # self.assertTrue(json_response[0]['resolved_url'].startswith(ENSEMBL_URL))

    # def test_resolve_redirect(self):
    #     stable_id = "ENSG00000127720.3"
    #     response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False)

    #     self.assertEqual(response.status_code, 307)  # Temporary Redirect
    #     self.assertIn("location", response.headers)
    #     self.assertTrue(response.headers["location"].endswith(f"/gene:{stable_id}"))

    # def test_resolve_multiple(self):
    #     stable_id = "ENSG00000127720" # returns multiple results
    #     response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False)
    #     self.assertEqual(response.status_code, 200)  # Multiple results in html page
    #     self.assertIn('beta.ensembl.org', response.text, 'Failed resolving multiple results')

    # def test_resolve_no_matches(self):
    #     stable_id = "ENSGXXX" # returns multiple results
    #     response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False)
    #     self.assertEqual(response.status_code, 404)

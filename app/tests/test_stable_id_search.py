# import unittest
# from unittest.mock import patch, MagicMock, Mock
# from fastapi.testclient import TestClient
# from core.config import ENSEMBL_URL
# from main import app
# import requests

# class TestResolverAPI(unittest.TestCase):
#     def setUp(self):
#         self.client = TestClient(app)
#         self.api_prefix = ""
#         self.mock_search_api_url = "/id" 

#     @patch("api.resources.resolver_view.requests.Session.post")
#     @patch("api.resources.resolver_view.requests.Session.get")
#     # @patch("requests.Session.post")
#     # @patch("requests.Session.get")
#     def test_resolve(self, mock_get, mock_post):
#         stable_id = "ENSG00000139618"
#         type = "gene"
#         app = "genome_browser"

#         # Mock search API
#         mock_post_response = MagicMock()
#         mock_post_response.status_code = 200
#         mock_post_response.raise_for_status = MagicMock()
#         mock_post_response_data = {
#             "matches": [
#                 {"genome_id": "genome1"},
#                 {"genome_id": "genome2"}
#             ]
#         }
#         mock_post_response.json.return_value = mock_post_response_data
        
#         mock_post.get.return_value = mock_post_response

#         # Mock metadata API
#         mock_get_response = MagicMock()
#         mock_get_response.status_code = 200
#         mock_get_response.raise_for_status = MagicMock()
#         mock_get_response_data = [
#             {
#                 "assembly": {"accession_id": "GCA_000001405.28", "name": "GRCh38"},
#                 "scientific_name": "Homo sapiens",
#                 "common_name": "Human",
#                 "type": "genome"
#             },
#             {
#                 "assembly": {"accession_id": "GCA_000001405.14", "name": "GRCh37"},
#                 "scientific_name": "Homo sapiens",
#                 "common_name": "Human",
#                 "type": "genome"
#             }
#         ]

#         mock_get_response.json.return_value = mock_get_response_data
#         mock_get.get.return_value = mock_get_response

#         self.assertEqual(mock_get_response.status_code, 200)
    
#         response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False, headers={"Accept": "application/json"},)
#     #     # response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False, headers={"Accept": "text/html"},)

#     #     # Assertions
#         self.assertEqual(response.status_code, 200)
#     #     self.assertIn('application/json', response.headers['content-type'])

#     #     json_response = response.json()
#     #     self.assertEqual(len(json_response), 2)
#     #     self.assertEqual(json_response[0]['accession_id'], "GCA_000001405.28")
#     #     self.assertEqual(json_response[0]['assembly_name'], "GRCh38")
#     #     self.assertEqual(json_response[0]['species'], "Homo sapiens")
#     #     self.assertEqual(json_response[0]['type'], "genome")
#     #     self.assertTrue(json_response[0]['resolved_url'].startswith(ENSEMBL_URL))

#     # # def test_resolve_redirect(self):
#     # #     stable_id = "ENSG00000127720.3"
#     # #     response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False)

#     # #     self.assertEqual(response.status_code, 307)  # Temporary Redirect
#     # #     self.assertIn("location", response.headers)
#     # #     self.assertTrue(response.headers["location"].endswith(f"/gene:{stable_id}"))

#     # # def test_resolve_multiple(self):
#     # #     stable_id = "ENSG00000127720" # returns multiple results
#     # #     response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False)
#     # #     self.assertEqual(response.status_code, 200)  # Multiple results in html page
#     # #     self.assertIn('beta.ensembl.org', response.text, 'Failed resolving multiple results')

#     # # def test_resolve_no_matches(self):
#     # #     stable_id = "ENSGXXX" # returns multiple results
#     # #     response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False)
#     # #     self.assertEqual(response.status_code, 404)

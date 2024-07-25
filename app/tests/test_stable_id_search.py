import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from main import app
# import requests

class TestResolverAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.api_prefix = ""
        self.mock_search_api_url = "/id" 

    def test_resolve_redirect(self):
        stable_id = "ENSG00000127720.3"
        response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False)

        self.assertEqual(response.status_code, 307)  # Temporary Redirect
        self.assertIn("location", response.headers)
        self.assertTrue(response.headers["location"].endswith(f"/gene:{stable_id}"))

    def test_resolve_multiple(self):
        stable_id = "ENSG00000127720" # returns multiple results
        response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False)
        self.assertEqual(response.status_code, 200)  # Multiple results in html page
        self.assertIn('beta.ensembl.org', response.text, 'Failed resolving multiple results')

    def test_resolve_no_matches(self):
        stable_id = "ENSGXXX" # returns multiple results
        response = self.client.get(f"{self.mock_search_api_url}/{stable_id}", follow_redirects=False)
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()

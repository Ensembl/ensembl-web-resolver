import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from main import app
import requests

class TestResolverAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.stable_id = "ENSG0001"
        self.mock_search_api_url = "http://mockapi/stable-id"

    @patch('requests.Session.post')
    def test_resolve_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
          "matches": [
            {
              "genome_id": "grch38"
            }
          ]
        }
        mock_post.return_value = mock_response

        response = self.client.get(f"/{self.stable_id}")

        self.assertEqual(response.status_code, 307)  # 307 Temporary Redirect
        self.assertIn("location", response.headers)
        self.assertTrue(response.headers["location"].endswith(f"/gene:{self.stable_id}"))

    @patch('requests.Session.post')
    def test_resolve_no_matches(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "matches": []
        }
        mock_post.return_value = mock_response

        response = self.client.get(f"/{self.stable_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"response": "No matches found"})

    @patch('requests.Session.post')
    def test_resolve_http_error(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        response = self.client.get(f"/{self.stable_id}")

        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()

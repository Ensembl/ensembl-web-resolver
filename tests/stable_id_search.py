import unittest, requests, json
import os

class TestSearchGenesAPI(unittest.TestCase):
  def setUp(self):
    self.params = {
      "query": "ENSG00000127720",
      "genome_ids": [],
      "page": 1,
      "per_page": 1,
      "type": "Gene"
    }
    self.url = os.environ.get('ENSEMBL_WEB_SEARCH_URL', 'http://0.0.0.0:8083/genes')
    
  def test_successful_post_request(self):
    response = requests.post(self.url, json=self.params)

    self.assertEqual(response.status_code, 200)

    response_data = response.json()
    self.assertIn("meta", response_data)
    self.assertIn("matches", response_data)
    
if __name__ == '__main__':
  unittest.main()

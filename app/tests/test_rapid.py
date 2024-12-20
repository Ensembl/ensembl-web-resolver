import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from core.config import ENSEMBL_URL
from main import app


class TestRapid(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.api_prefix = ""
        self.mock_rapid_api_url = "/rapid"
        self.species_url_name = "Human_GCA_123.1"
        self.species_url_name_refseq = "DogRefSeq_GCA_123.1rs"

        self.mock_genome_id_response1 = {
            "genome_uuid": "genome_uuid1",
            "release_version": 110,
            "genome_tag": "",
        }

        self.mock_genome_id_response2 = {
            "genome_uuid": "genome_uuid2",
            "release_version": 110,
            "genome_tag": "xyz",
        }

        self.mock_ncbi_accession = "GCF_000001405.40"

        self.mock_resolved_url = {
            "genome1": f"{ENSEMBL_URL}/species/genome_uuid1",
            "genome2": f"{ENSEMBL_URL}/species/xyz",
        }

    @patch("api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    @patch("api.resources.rapid_view.format_assembly_accession")
    def test_rapid_species_home_success(
        self,
        mock_format_assembly_accession,
        mock_get_genome_id_from_assembly_accession_id,
    ):

        # test web-metadata-api response without genome_tag
        mock_get_genome_id_from_assembly_accession_id.return_value = (
            self.mock_genome_id_response1
        )
        mock_format_assembly_accession.return_value = self.mock_ncbi_accession

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 307)  # Temporary Redirect
        self.assertIn("location", response.headers)
        self.assertEqual(
            response.headers["location"], self.mock_resolved_url["genome1"]
        )

        # test web-metadata-api response with genome_tag
        mock_get_genome_id_from_assembly_accession_id.return_value = (
            self.mock_genome_id_response2
        )

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 307)  # Temporary Redirect
        self.assertIn("location", response.headers)
        self.assertEqual(
            response.headers["location"], self.mock_resolved_url["genome2"]
        )

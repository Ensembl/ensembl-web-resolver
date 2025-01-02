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

    # Test species home page
    @patch("api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    def test_rapid_species_home_success(
        self, mock_get_genome_id_from_assembly_accession_id
    ):

        # test web-metadata-api response without genome_tag
        mock_get_genome_id_from_assembly_accession_id.return_value = (
            self.mock_genome_id_response1
        )

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

    # Test Region in detail page
    @patch("api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    def test_rapid_species_location_success(
        self, mock_get_genome_id_from_assembly_accession_id
    ):

        # test web-metadata-api response without genome_tag
        mock_get_genome_id_from_assembly_accession_id.return_value = (
            self.mock_genome_id_response1
        )

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/Location/View",
            params={"r": "1:1000-2000"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 307)  # Redirect
        self.assertIn(
            f"{ENSEMBL_URL}/genome-browser/genome_uuid1?focus=location:1:1000-2000",
            response.headers["location"],
        )

    # Test Gene pages
    @patch("api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    def test_rapid_species_gene_compara_homolog(
        self, mock_get_genome_id_from_assembly_accession_id
    ):
        mock_get_genome_id_from_assembly_accession_id.return_value = (
            self.mock_genome_id_response1
        )

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/Gene/Compara_Homolog",
            params={"g": "GENE123"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 307)  # Redirect
        self.assertIn(
            f"{ENSEMBL_URL}/entity-viewer/genome_uuid1/gene:GENE123?view=homology",
            response.headers["location"],
        )

    # Test 404
    @patch("api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    def test_rapid_species_404_not_found(
        self, mock_get_genome_id_from_assembly_accession_id
    ):
        mock_get_genome_id_from_assembly_accession_id.return_value = {}

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/Invalid_GCA"
        )
        self.assertEqual(response.status_code, 404)

    # Test invalid url entity
    def test_rapid_species_422_unprocessable_entity(self):
        response = self.client.get(f"{self.mock_rapid_api_url}/Invalid_Name/")
        self.assertEqual(response.status_code, 422)

    # Test POST
    def test_rapid_species_post_method_not_allowed(self):
        response = self.client.post(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/"
        )
        self.assertEqual(response.status_code, 405)

    # Test 500
    @patch("api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    def test_rapid_species_500_internal_server_error(
        self, mock_get_genome_id_from_assembly_accession_id
    ):
        mock_get_genome_id_from_assembly_accession_id.return_value = (
            self.mock_genome_id_response1
        )

        mock_get_genome_id_from_assembly_accession_id.side_effect = Exception(
            "Unexpected error"
        )

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/"
        )
        self.assertEqual(response.status_code, 500)

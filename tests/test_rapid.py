import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.api.models.resolver import RapidResolverResponse
from app.core.config import ENSEMBL_URL
from app.main import app


class TestRapid(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.api_prefix = ""
        self.mock_rapid_api_url = "/rapid"
        self.stable_id = "ENSAROG00010015245"
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
    
    # Test rapid home page
    def test_rapid_home_success(self):
        # test with accept header for JSON response
        response = self.client.get(
            f"{self.mock_rapid_api_url}/",
            headers={"accept": "application/json"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 200)  # OK
        self.assertEqual(
            response.json(),
            RapidResolverResponse(resolved_url=ENSEMBL_URL).model_dump(mode='json')
        )


    # Test rapid help page
    def test_rapid_help_success(self):
        # test with accept header for JSON response
        response = self.client.get(
            f"{self.mock_rapid_api_url}/info/index.html",
            headers={"accept": "application/json"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 200)  # OK
        self.assertEqual(
            response.json(),
            RapidResolverResponse(resolved_url=f"{ENSEMBL_URL}/help").model_dump(mode='json')
        )


    # Test rapid blast page
    def test_rapid_blast_success(self):
        # test with accept header for JSON response
        response1 = self.client.get(
            f"{self.mock_rapid_api_url}/Multi/Tools/Blast",
            headers={"accept": "application/json"},
            follow_redirects=False,
        )
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(
            response1.json(),
            RapidResolverResponse(resolved_url=f"{ENSEMBL_URL}/blast").model_dump(mode='json')
        )

        response2 = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/Tools/Blast",
            headers={"accept": "application/json"},
            follow_redirects=False,
        )
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(
            response2.json(),
            RapidResolverResponse(resolved_url=f"{ENSEMBL_URL}/blast").model_dump(mode='json')
        )


    # Test species home page
    @patch("app.api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    def test_rapid_species_home_success(
        self, mock_get_genome_id_from_assembly_accession_id
    ):
        # test with accept header for JSON response
        mock_get_genome_id_from_assembly_accession_id.return_value = (
            self.mock_genome_id_response1
        )

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/",
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)  # OK
        self.assertEqual(
            response.json(), 
            RapidResolverResponse(resolved_url = self.mock_resolved_url["genome1"]).model_dump(mode='json')
        )


    # Test Region in detail page
    @patch("app.api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    def test_rapid_species_location_success(
        self, mock_get_genome_id_from_assembly_accession_id
    ):
        # test with accept header for JSON response
        mock_get_genome_id_from_assembly_accession_id.return_value = (
            self.mock_genome_id_response1
        )

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/Location/View",
            params={"r": "1:1000-2000"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)  # OK
        self.assertEqual(
            response.json(), 
            RapidResolverResponse(resolved_url = f"{ENSEMBL_URL}/genome-browser/genome_uuid1?focus=location:1:1000-2000").model_dump(mode='json')
        )

    # Test Gene pages
    @patch("app.api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    def test_rapid_species_gene_compara_homolog(
        self, mock_get_genome_id_from_assembly_accession_id
    ):
        # test with accept header for JSON response
        mock_get_genome_id_from_assembly_accession_id.return_value = (
            self.mock_genome_id_response1
        )

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/Gene/Compara_Homolog",
            params={"g": "GENE123"},
            follow_redirects=False,
            headers={"accept": "application/json"},
        )

        self.assertEqual(response.status_code, 200)  # OK
        self.assertEqual(
            response.json(),
            RapidResolverResponse(
                resolved_url=f"{ENSEMBL_URL}/entity-viewer/genome_uuid1/gene:GENE123?view=homology"
            ).model_dump(mode='json'),
        )

    # Test 404
    @patch("app.api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
    def test_rapid_species_404_not_found(
        self, mock_get_genome_id_from_assembly_accession_id
    ):
        mock_get_genome_id_from_assembly_accession_id.return_value = {}

        response = self.client.get(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/Invalid_GCA",
            headers={"accept": "application/json"},
        )
        self.assertEqual(response.status_code, 404)

    # Test invalid url entity
    def test_rapid_species_422_unprocessable_entity(self):
        response = self.client.get(f"{self.mock_rapid_api_url}/Invalid_Name/", headers={"accept": "application/json"},)
        self.assertEqual(response.status_code, 422)

    # Test POST
    def test_rapid_species_post_method_not_allowed(self):
        response = self.client.post(
            f"{self.mock_rapid_api_url}/{self.species_url_name}/",
            headers={"accept": "application/json"},
        )
        self.assertEqual(response.status_code, 405)

    # Test 500
    @patch("app.api.resources.rapid_view.get_genome_id_from_assembly_accession_id")
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
            f"{self.mock_rapid_api_url}/{self.species_url_name}/",
            headers={"accept": "application/json"},
        )
        self.assertEqual(response.status_code, 500)


    @patch("app.api.resources.rapid_view.get_search_results")
    def test_rapid_id_resolve_404(self, mock_get_search_results):

        mock_get_search_results.return_value = {}

        response = self.client.get(
            f"{self.mock_rapid_api_url}/id/{self.stable_id}", follow_redirects=False,
            headers = {"accept": "application/json"}
        )
        self.assertEqual(response.status_code, 404)

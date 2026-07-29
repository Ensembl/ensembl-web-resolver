import unittest
from unittest.mock import MagicMock, patch

from app.api.utils.metadata import get_assembly_accession_id_from_genome_id
from app.core.config import ENSEMBL_URL


class TestMetadata(unittest.TestCase):
    @patch("app.api.utils.metadata.requests.Session")
    def test_get_assembly_accession_id_from_genome_id(self, mock_session_class):
        genome_id = "genome_uuid1"
        response = MagicMock()
        response.json.return_value = {"assembly": {"accession_id": "GCA_01234567.1"}}
        session = mock_session_class.return_value
        session.get.return_value.__enter__.return_value = response

        accession_id = get_assembly_accession_id_from_genome_id(genome_id)

        self.assertEqual(accession_id, "GCA_01234567.1")
        session.get.assert_called_once_with(
            url=f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/explain",
            timeout=10,
        )
        response.raise_for_status.assert_called_once_with()

    @patch("app.api.utils.metadata.requests.Session")
    def test_get_assembly_accession_id_returns_none_when_accession_is_absent(
        self, mock_session_class
    ):
        response = MagicMock()
        response.json.return_value = {"assembly": {}}
        mock_session_class.return_value.get.return_value.__enter__.return_value = response

        accession_id = get_assembly_accession_id_from_genome_id("genome_uuid1")

        self.assertIsNone(accession_id)

    @patch("app.api.utils.metadata.requests.Session")
    def test_get_assembly_accession_id_wraps_endpoint_errors(self, mock_session_class):
        response = MagicMock()
        response.raise_for_status.side_effect = Exception("503 Server Error")
        mock_session_class.return_value.get.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(
            Exception,
            "Failed to fetch assembly accession for genome 'genome_uuid1': 503 Server Error",
        ):
            get_assembly_accession_id_from_genome_id("genome_uuid1")


if __name__ == "__main__":
    unittest.main()

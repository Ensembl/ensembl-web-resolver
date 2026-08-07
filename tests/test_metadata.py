import unittest
from unittest.mock import MagicMock, patch

from app.api.utils.metadata import (
    get_genome_tag_from_genome_id,
    search_variant,
)
from app.core.config import ENSEMBL_URL


class TestMetadata(unittest.TestCase):
    @patch("app.api.utils.metadata.requests.Session")
    def test_get_genome_tag_from_genome_id(self, mock_session_class):
        genome_id = "genome_uuid1"
        response = MagicMock()
        response.json.return_value = {"genome_tag": "GCA_01234567.1"}
        session = mock_session_class.return_value
        session.get.return_value.__enter__.return_value = response

        genome_tag = get_genome_tag_from_genome_id(genome_id)

        self.assertEqual(genome_tag, "GCA_01234567.1")
        session.get.assert_called_once_with(
            url=f"{ENSEMBL_URL}/api/metadata/genome/{genome_id}/explain",
            timeout=10,
        )
        response.raise_for_status.assert_called_once_with()

    @patch("app.api.utils.metadata.requests.Session")
    def test_get_genome_tag_returns_none_when_tag_is_absent(self, mock_session_class):
        response = MagicMock()
        response.json.return_value = {}
        mock_session_class.return_value.get.return_value.__enter__.return_value = (
            response
        )

        genome_tag = get_genome_tag_from_genome_id("genome_uuid1")

        self.assertIsNone(genome_tag)

    @patch("app.api.utils.metadata.requests.Session")
    def test_get_genome_tag_wraps_endpoint_errors(self, mock_session_class):
        response = MagicMock()
        response.raise_for_status.side_effect = Exception("503 Server Error")
        mock_session_class.return_value.get.return_value.__enter__.return_value = (
            response
        )

        with self.assertRaisesRegex(
            Exception,
            "Failed to fetch genome tag for genome 'genome_uuid1': 503 Server Error",
        ):
            get_genome_tag_from_genome_id("genome_uuid1")

    @patch("app.api.utils.metadata.requests.Session")
    def test_search_variant_posts_genome_and_variant_id(self, mock_session_class):
        genome_id = "genome_uuid1"
        response = MagicMock()
        response.json.return_value = {
            "matches": [
                {
                    "variant_name": "rs99",
                    "genome_id": genome_id,
                    "region_name": "7",
                    "start": 24399036,
                }
            ]
        }
        session = mock_session_class.return_value
        session.post.return_value.__enter__.return_value = response

        result = search_variant(genome_id, "rs99")

        self.assertEqual(result, response.json.return_value["matches"][0])
        session.post.assert_called_once_with(
            url=f"{ENSEMBL_URL}/api/search/variants",
            json={"genome_ids": [genome_id], "query": "rs99"},
            timeout=10,
        )
        response.raise_for_status.assert_called_once_with()

    @patch("app.api.utils.metadata.requests.Session")
    def test_search_variant_returns_none_when_no_matches(self, mock_session_class):
        response = MagicMock()
        response.json.return_value = {"matches": []}
        mock_session_class.return_value.post.return_value.__enter__.return_value = (
            response
        )

        self.assertIsNone(search_variant("genome_uuid1", "rs99"))


if __name__ == "__main__":
    unittest.main()

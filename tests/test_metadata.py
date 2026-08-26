import unittest
from unittest.mock import MagicMock, patch

import requests

from app.api.utils.metadata import (
    MetadataNotFoundError,
    get_metadata,
    get_genome_tag_from_genome_id,
    search_variant,
)
from app.core.config import ENSEMBL_URL


class TestMetadata(unittest.TestCase):
    @patch("app.api.utils.metadata.requests.Session")
    def test_get_metadata_keeps_highest_priority_match_per_genome(
        self, mock_session_class
    ):
        response = MagicMock()
        response.json.side_effect = lambda: {"assembly": None}
        mock_session_class.return_value.get.return_value.__enter__.return_value = (
            response
        )
        matches = [
            {"genome_id": "genome-1", "type": "protein"},
            {"genome_id": "genome-1", "type": "transcript"},
            {"genome_id": "genome-2", "type": "protein"},
            {"genome_id": "genome-2", "type": "gene"},
        ]

        result = get_metadata(matches)

        self.assertEqual(
            [result[genome]["stable_id_type"] for genome in ("genome-1", "genome-2")],
            ["transcript", "gene"],
        )
        self.assertEqual(mock_session_class.call_count, 2)

    @patch("app.api.utils.metadata.requests.Session")
    def test_get_metadata_keeps_latest_integrated_release_per_assembly(
        self, mock_session_class
    ):
        responses = {
            "genome-38-integrated": {
                "assembly": {"accession_id": "GCA-38", "name": "GRCh38"},
                "release": {"type": "integrated", "name": "2026-07"},
            },
            "genome-38-partial": {
                "assembly": {"accession_id": "GCA-38", "name": "GRCh38"},
                "release": {"type": "partial", "name": "2026-04-09"},
            },
            "genome-38-newer-partial": {
                "assembly": {"accession_id": "GCA-38", "name": "GRCh38"},
                "release": {"type": "partial", "name": "2026-08"},
            },
            "genome-38-archive": {
                "assembly": {"accession_id": "GCA-38", "name": "GRCh38"},
                "release": {"type": "archive", "name": "2025-02"},
            },
            "genome-37-integrated": {
                "assembly": {"accession_id": "GCA-37", "name": "GRCh37"},
                "release": {"type": "integrated", "name": "2026-07"},
            },
        }

        def response_for_genome(url, timeout):
            response = MagicMock()
            genome_id = url.split("/genome/")[1].split("/")[0]
            response.json.return_value = responses[genome_id]
            context = MagicMock()
            context.__enter__.return_value = response
            return context

        mock_session_class.return_value.get.side_effect = response_for_genome
        matches = [{"genome_id": genome_id} for genome_id in responses]

        result = get_metadata(matches)

        self.assertEqual(
            list(result),
            ["genome-38-integrated", "genome-38-newer-partial", "genome-37-integrated"],
        )

    @patch("app.api.utils.metadata.requests.Session")
    def test_get_metadata_prefers_reference_results(self, mock_session_class):
        responses = {
            "genome-38": {
                "assembly": {"accession_id": "GCA-38", "name": "GRCh38"},
                "is_reference": True,
                "release": {"type": "integrated", "name": "2026-07"},
            },
            "genome-37": {
                "assembly": {"accession_id": "GCA-37", "name": "GRCh37"},
                "is_reference": False,
                "release": {"type": "integrated", "name": "2026-07"},
            },
        }

        def response_for_genome(url, timeout):
            response = MagicMock()
            genome_id = url.split("/genome/")[1].split("/")[0]
            response.json.return_value = responses[genome_id]
            context = MagicMock()
            context.__enter__.return_value = response
            return context

        mock_session_class.return_value.get.side_effect = response_for_genome

        result = get_metadata([{"genome_id": genome_id} for genome_id in responses])

        self.assertEqual(list(result), ["genome-38"])

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
    def test_get_genome_tag_raises_not_found_for_a_missing_genome(
        self, mock_session_class
    ):
        response = MagicMock(status_code=404)
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
        mock_session_class.return_value.get.return_value.__enter__.return_value = (
            response
        )

        with self.assertRaisesRegex(
            MetadataNotFoundError,
            "Genome 'genome_uuid1' was not found in the metadata API",
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

    @patch("app.api.utils.metadata.requests.Session")
    def test_search_variant_returns_none_when_endpoint_returns_404(
        self, mock_session_class
    ):
        response = MagicMock(status_code=404)
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
        mock_session_class.return_value.post.return_value.__enter__.return_value = (
            response
        )

        self.assertIsNone(search_variant("genome_uuid1", "rs99"))


if __name__ == "__main__":
    unittest.main()

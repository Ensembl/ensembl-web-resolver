import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.api.models.resolver import SearchPayload
from app.api.utils.search import get_search_results


class TestFastMatchSearch(unittest.TestCase):
    def setUp(self):
        self.params = SearchPayload(
            stable_id="ENSG00000127720.3", type="gene", per_page=10
        )

    @patch("app.api.utils.search.get_search_hub_results")
    @patch("app.api.utils.search.FAST_MATCH_ENABLED", False)
    def test_uses_search_hub_when_fast_match_is_disabled(self, mock_search_hub):
        mock_search_hub.return_value = {"matches": []}

        self.assertEqual(get_search_results(self.params), {"matches": []})
        mock_search_hub.assert_called_once_with(self.params)

    @patch("app.api.utils.search.get_search_hub_results")
    @patch("app.api.utils.search.fm_py")
    @patch("app.api.utils.search.FAST_MATCH_ENABLED", True)
    @patch("app.api.utils.search.FAST_MATCH_DB_PATH", "/data/stable-ids.redb")
    def test_falls_back_to_search_hub_when_fast_match_fails(
        self, mock_fm_py, mock_search_hub
    ):
        mock_fm_py.find_key.side_effect = RuntimeError("Unable to open file")
        mock_search_hub.return_value = {"matches": [{"genome_id": "genome-1"}]}

        self.assertEqual(
            get_search_results(self.params),
            {"matches": [{"genome_id": "genome-1"}]},
        )
        mock_search_hub.assert_called_once_with(self.params)

    @patch("app.api.utils.search.fm_py")
    @patch("app.api.utils.search.FAST_MATCH_ENABLED", True)
    @patch("app.api.utils.search.FAST_MATCH_DB_PATH", "/data/stable-ids.redb")
    def test_returns_matches_with_unversioned_stable_id(self, mock_fm_py):
        mock_fm_py.find_key.return_value = "genome-1|gene|+genome-2|gene|"

        result = get_search_results(self.params)

        self.assertEqual(
            result,
            {
                "matches": [
                    {
                        "genome_id": "genome-1",
                        "unversioned_stable_id": "ENSG00000127720",
                        "type": "gene",
                        "parent_transcript_id": None,
                    },
                    {
                        "genome_id": "genome-2",
                        "unversioned_stable_id": "ENSG00000127720",
                        "type": "gene",
                        "parent_transcript_id": None,
                    },
                ]
            },
        )
        mock_fm_py.find_key.assert_called_once_with(
            "ENSG00000127720.3", "/data/stable-ids.redb"
        )

    @patch("app.api.utils.search.fm_py")
    @patch("app.api.utils.search.FAST_MATCH_ENABLED", True)
    @patch("app.api.utils.search.FAST_MATCH_DB_PATH", "/data/stable-ids.redb")
    def test_filters_other_document_types_and_duplicate_genomes(self, mock_fm_py):
        mock_fm_py.find_key.return_value = (
            "genome-1|transcript|+genome-2|gene|+genome-2|gene|"
        )

        result = get_search_results(self.params)

        self.assertEqual(
            result,
            {
                "matches": [
                    {
                        "genome_id": "genome-2",
                        "unversioned_stable_id": "ENSG00000127720",
                        "type": "gene",
                        "parent_transcript_id": None,
                    }
                ]
            },
        )

    @patch("app.api.utils.search.fm_py")
    @patch("app.api.utils.search.FAST_MATCH_ENABLED", True)
    @patch("app.api.utils.search.FAST_MATCH_DB_PATH", "/data/stable-ids.redb")
    def test_returns_supported_types_when_no_type_filter_is_supplied(self, mock_fm_py):
        mock_fm_py.find_key.return_value = "genome-1|gene|+genome-1|transcript|"
        params = SearchPayload(stable_id="ENSX000001", type=None, per_page=10)

        result = get_search_results(params)

        self.assertEqual(
            result,
            {
                "matches": [
                    {
                        "genome_id": "genome-1",
                        "unversioned_stable_id": "ENSX000001",
                        "type": "gene",
                        "parent_transcript_id": None,
                    },
                    {
                        "genome_id": "genome-1",
                        "unversioned_stable_id": "ENSX000001",
                        "type": "transcript",
                        "parent_transcript_id": None,
                    },
                ]
            },
        )

    @patch("app.api.utils.search.fm_py")
    @patch("app.api.utils.search.FAST_MATCH_ENABLED", True)
    @patch("app.api.utils.search.FAST_MATCH_DB_PATH", "/data/stable-ids.redb")
    def test_returns_parent_transcript_for_a_protein(self, mock_fm_py):
        mock_fm_py.find_key.return_value = (
            "1e539c0e-df18-46aa-96eb-d8fafd40a8e6|protein|OsAzu_11g0000590.01"
        )
        params = SearchPayload(stable_id="OsAzu_11g0000590.01.p", type=None)

        self.assertEqual(
            get_search_results(params),
            {
                "matches": [
                    {
                        "genome_id": "1e539c0e-df18-46aa-96eb-d8fafd40a8e6",
                        "unversioned_stable_id": "OsAzu_11g0000590.01.p",
                        "type": "protein",
                        "parent_transcript_id": "OsAzu_11g0000590.01",
                    }
                ]
            },
        )

    @patch("app.api.utils.search.fm_py")
    @patch("app.api.utils.search.FAST_MATCH_ENABLED", True)
    @patch("app.api.utils.search.FAST_MATCH_DB_PATH", "/data/stable-ids.redb")
    def test_preserves_dotted_species_specific_stable_ids(self, mock_fm_py):
        mock_fm_py.find_key.return_value = "genome-1|transcript|"
        stable_id = "OsAzu_12g0006100.01"
        params = SearchPayload(stable_id=stable_id, type="transcript")

        result = get_search_results(params)

        self.assertEqual(
            result["matches"][0]["unversioned_stable_id"], stable_id
        )

    @patch("app.api.utils.search.fm_py")
    @patch("app.api.utils.search.FAST_MATCH_ENABLED", True)
    @patch("app.api.utils.search.FAST_MATCH_DB_PATH", "/data/stable-ids.redb")
    def test_returns_empty_matches_for_a_miss(self, mock_fm_py):
        mock_fm_py.find_key.return_value = None

        self.assertEqual(get_search_results(self.params), {"matches": []})

    @patch(
        "app.api.utils.search.fm_py",
        SimpleNamespace(find_key=lambda *_: "bad-value"),
    )
    @patch("app.api.utils.search.get_search_hub_results")
    @patch("app.api.utils.search.FAST_MATCH_ENABLED", True)
    @patch("app.api.utils.search.FAST_MATCH_DB_PATH", "/data/stable-ids.redb")
    def test_falls_back_to_search_hub_for_malformed_index_values(self, mock_search_hub):
        mock_search_hub.return_value = {"matches": []}

        self.assertEqual(get_search_results(self.params), {"matches": []})
        mock_search_hub.assert_called_once_with(self.params)

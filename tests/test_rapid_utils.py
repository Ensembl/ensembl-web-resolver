import unittest
from unittest.mock import MagicMock
from fastapi import Request

from app.api.utils.rapid import construct_rapid_archive_url
from app.core.config import RAPID_ARCHIVE_URL


class TestRapidUtils(unittest.TestCase):
    def _assert_rapid_url(self, rapid_path, query_string=""):
        req = MagicMock(spec=Request)
        req.url.path = f"/rapid/{rapid_path}"
        req.url.query = query_string
        res = construct_rapid_archive_url(req)
        expected_url = RAPID_ARCHIVE_URL if not rapid_path else f"{RAPID_ARCHIVE_URL}/{rapid_path}"
        if query_string:
            expected_url = f"{expected_url}?{query_string}"
        self.assertEqual(res, expected_url)

    def test_construct_rapid_archive_url(self):
        self._assert_rapid_url("")
        self._assert_rapid_url("info/index.html")
        self._assert_rapid_url("Multi/Tools/Blast")
        self._assert_rapid_url("Homo_sapiens_GCA_009914755.4/Tools/Blast")
        self._assert_rapid_url("id/ENSG00000221914.11")
        self._assert_rapid_url("Camarhynchus_parvulus_GCA_902806625.1")
        self._assert_rapid_url("Camarhynchus_parvulus_GCA_902806625.1/Location/Genome")
        self._assert_rapid_url("Homo_sapiens_GCA_009914755.4/Location/View", "r=1:56873660-58424710")
        self._assert_rapid_url("Homo_sapiens_GCA_009914755.4/Gene/Summary", "r=1:56873660-58424710")

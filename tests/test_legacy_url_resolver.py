import unittest
from uuid import UUID
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.utils.species_mapping import (
    SpeciesGenomeUuidNotFoundError,
    SpeciesMappingNotFoundError,
    SpeciesNotFoundError,
)
from app.core.config import APP_PREFIX, ENSEMBL_URL, STATIC_PATH
from app.main import app


class TestUrlResolver(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        api_prefix = "" if APP_PREFIX == "/" else APP_PREFIX
        self.mock_url_resolver_api_url = f"{api_prefix}/legacy"
        self.genome_uuid = "genome_uuid1"
        self.genome_tag = "GCA_01234567.1"
        self.static_mapping_patcher = patch(
            "app.api.resources.legacy_url_resolver_view.get_static_legacy_url_mapping"
        )
        self.mock_static_mapping = self.static_mapping_patcher.start()
        self.mock_static_mapping.return_value = None
        self.genome_tag_patcher = patch(
            "app.api.resources.legacy_url_resolver_view.get_genome_tag_from_genome_id"
        )
        self.mock_genome_tag_lookup = self.genome_tag_patcher.start()
        self.mock_genome_tag_lookup.return_value = self.genome_tag
        self.variant_search_patcher = patch(
            "app.api.resources.legacy_url_resolver_view.search_variant"
        )
        self.mock_variant_search = self.variant_search_patcher.start()
        self.mock_variant_search.return_value = None

    def tearDown(self):
        self.static_mapping_patcher.stop()
        self.genome_tag_patcher.stop()
        self.variant_search_patcher.stop()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_static_path_mapping_with_redirect(self, mock_species_lookup):
        """Resolve configured static legacy paths before species URL rules."""
        self.mock_static_mapping.return_value = "https://www.ensembl.org/tools/blast"

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://staging-plants.ensembl.org/Multi/Tools/Blast/"
                    "?discard=this"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://www.ensembl.org/tools/blast",
        )
        self.assertEqual(response.headers["cache-control"], "no-store, max-age=0")
        self.mock_static_mapping.assert_called_once_with(
            "https://staging-plants.ensembl.org/Multi/Tools/Blast/?discard=this"
        )
        mock_species_lookup.assert_not_called()
        self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.record_legacy_url_resolver_outcome"
    )
    def test_records_resolved_outcome(self, mock_record_outcome):
        """Record successful browser redirects as resolved."""
        self.mock_static_mapping.return_value = "https://www.ensembl.org/tools/blast"

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://staging.ensembl.org/Multi/Tools/Blast/"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        mock_record_outcome.assert_called_once_with("resolved", "html")

    @patch(
        "app.api.resources.legacy_url_resolver_view.record_legacy_url_resolver_outcome"
    )
    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_records_archive_fallback_outcome(
        self, mock_species_lookup, mock_record_outcome
    ):
        """Record redirects to an archive as archive fallbacks."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG1"
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        mock_record_outcome.assert_called_once_with("archive_fallback", "html")

    @patch(
        "app.api.resources.legacy_url_resolver_view.record_legacy_url_resolver_outcome"
    )
    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_records_archive_fallback_outcome_for_unresolved_browser_url(
        self, mock_species_lookup, mock_record_outcome
    ):
        """Record immediate archive redirects for unresolved browser URLs."""
        mock_species_lookup.side_effect = SpeciesMappingNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/foo"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"], "https://jun2026.archive.ensembl.org/foo"
        )
        mock_record_outcome.assert_called_once_with("archive_fallback", "html")

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_static_host_mapping_with_json_response(self, mock_species_lookup):
        """Return configured static host mappings for JSON clients."""
        self.mock_static_mapping.return_value = "https://www.ensembl.org"

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "staging-protists.ensembl.org"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"resolved_url": "https://www.ensembl.org"},
        )
        self.assertEqual(response.headers["cache-control"], "no-store, max-age=0")
        self.mock_static_mapping.assert_called_once_with("staging-protists.ensembl.org")
        mock_species_lookup.assert_not_called()
        self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_info_paths_to_archive_hosts(self, mock_species_lookup):
        """Redirect generic info paths to the matching archive host."""
        test_cases = [
            (
                "https://staging.ensembl.org/info/index.html",
                "https://jun2026.archive.ensembl.org/info/index.html",
            ),
            (
                "https://staging-plants.ensembl.org/info/index.html",
                "https://eg63-plants.ensembl.org/info/index.html",
            ),
            (
                "https://staging-fungi.ensembl.org/info/index.html",
                "https://eg63-fungi.ensembl.org/info/index.html",
            ),
            (
                "https://staging-bacteria.ensembl.org/info/index.html",
                "https://eg63-bacteria.ensembl.org/info/index.html",
            ),
            (
                "https://staging-metazoa.ensembl.org/info/index.html",
                "https://eg63-metazoa.ensembl.org/info/index.html",
            ),
            (
                "https://staging-protists.ensembl.org/info/index.html",
                "https://eg63-protists.ensembl.org/info/index.html",
            ),
        ]

        for legacy_url, expected_url in test_cases:
            with self.subTest(legacy_url=legacy_url):
                self.mock_static_mapping.reset_mock()
                mock_species_lookup.reset_mock()

                response = self.client.get(
                    self.mock_url_resolver_api_url,
                    params={"url": legacy_url},
                    headers={"accept": "application/json"},
                    follow_redirects=False,
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"resolved_url": expected_url})
                self.mock_static_mapping.assert_not_called()
                mock_species_lookup.assert_not_called()
                self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_info_archive_preserves_query_and_fragment(
        self, mock_species_lookup
    ):
        """Preserve query strings and fragments for generic info archive URLs."""
        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://staging.ensembl.org/info/docs/tools/vep/index.html"
                    "?foo=bar#content"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            (
                "https://jun2026.archive.ensembl.org"
                "/info/docs/tools/vep/index.html?foo=bar#content"
            ),
        )
        self.mock_static_mapping.assert_not_called()
        mock_species_lookup.assert_not_called()
        self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_gene_phenotype_paths_redirect_to_archive(
        self, mock_species_lookup
    ):
        """Redirect unsupported gene phenotype pages to their archives."""
        test_cases = [
            (
                "https://staging.ensembl.org/Homo_sapiens/Gene/Phenotype"
                "?g=ENSG00000012048",
                "https://jun2026.archive.ensembl.org/Homo_sapiens/Gene/Phenotype"
                "?g=ENSG00000012048",
            ),
            (
                "https://staging-plants.ensembl.org/Triticum_aestivum/Gene/Phenotype"
                "?g=TraesCS3D02G273600",
                "https://eg63-plants.ensembl.org/Triticum_aestivum/Gene/Phenotype"
                "?g=TraesCS3D02G273600",
            ),
        ]

        for legacy_url, expected_url in test_cases:
            with self.subTest(legacy_url=legacy_url):
                self.mock_static_mapping.reset_mock()
                mock_species_lookup.reset_mock()

                response = self.client.get(
                    self.mock_url_resolver_api_url,
                    params={"url": legacy_url},
                    follow_redirects=False,
                )

                self.assertEqual(response.status_code, 308)
                self.assertEqual(response.headers["location"], expected_url)
                mock_species_lookup.assert_not_called()
                self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_gene_compara_paths_redirect_to_archive(
        self, mock_species_lookup
    ):
        """Redirect unsupported legacy Compara pages to their archives."""
        archive_hosts = [
            ("staging.ensembl.org", "jun2026.archive.ensembl.org"),
            ("staging-plants.ensembl.org", "eg63-plants.ensembl.org"),
            ("staging-metazoa.ensembl.org", "eg63-metazoa.ensembl.org"),
            ("staging-fungi.ensembl.org", "eg63-fungi.ensembl.org"),
            ("staging-protists.ensembl.org", "eg63-protists.ensembl.org"),
            ("staging-bacteria.ensembl.org", "eg63-bacteria.ensembl.org"),
        ]

        for page in ("Compara_Ortholog", "Compara_Paralog"):
            for source_host, archive_host in archive_hosts:
                with self.subTest(page=page, source_host=source_host):
                    mock_species_lookup.reset_mock()
                    response = self.client.get(
                        self.mock_url_resolver_api_url,
                        params={
                            "url": (
                                f"https://{source_host}/Homo_sapiens/Gene/{page}"
                                "?g=ENSG00000012048"
                            )
                        },
                        follow_redirects=False,
                    )

                    self.assertEqual(response.status_code, 308)
                    self.assertEqual(
                        response.headers["location"],
                        f"https://{archive_host}/Homo_sapiens/Gene/{page}"
                        "?g=ENSG00000012048",
                    )
                    mock_species_lookup.assert_not_called()
                    self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_species_scoped_blast_to_blast_tool(self, mock_species_lookup):
        """Resolve legacy species-scoped BLAST URLs to the shared BLAST tool."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://staging.ensembl.org/Homo_sapiens/Multi/Tools/Blast"
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"resolved_url": f"{ENSEMBL_URL}/tools/blast"}
        )
        mock_species_lookup.assert_called_once_with("Homo_sapiens")

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_species_scoped_vep_to_division_archive(self, mock_species_lookup):
        """Resolve species-scoped VEP URLs to the matching division archive."""
        test_cases = [
            ("staging.ensembl.org", "jun2026.archive.ensembl.org"),
            ("staging-plants.ensembl.org", "eg63-plants.ensembl.org"),
            ("staging-metazoa.ensembl.org", "eg63-metazoa.ensembl.org"),
            ("staging-fungi.ensembl.org", "eg63-fungi.ensembl.org"),
            ("staging-protists.ensembl.org", "eg63-protists.ensembl.org"),
            ("staging-bacteria.ensembl.org", "eg63-bacteria.ensembl.org"),
        ]

        for source_host, archive_host in test_cases:
            with self.subTest(source_host=source_host):
                self.mock_static_mapping.reset_mock()
                mock_species_lookup.reset_mock()

                response = self.client.get(
                    self.mock_url_resolver_api_url,
                    params={
                        "url": (
                            f"https://{source_host}/Homo_sapiens/Tools/VEP"
                            "?foo=bar#content"
                        )
                    },
                    headers={"accept": "application/json"},
                    follow_redirects=False,
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(),
                    {
                        "resolved_url": (
                            f"https://{archive_host}/Homo_sapiens/Tools/VEP"
                            "?foo=bar#content"
                        )
                    },
                )
                self.mock_static_mapping.assert_not_called()
                mock_species_lookup.assert_not_called()
                self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_info_unknown_host_does_not_redirect(self, mock_species_lookup):
        """Return an error for unknown info hosts instead of guessing an archive."""
        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://example.org/info/index.html"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("location", response.headers)
        self.mock_static_mapping.assert_not_called()
        mock_species_lookup.assert_not_called()
        self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_species_home_with_json_response(self, mock_species_lookup):
        """Resolve a species home URL to the new Ensembl genome page."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Homo_sapiens/Info/Index"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"resolved_url": f"{ENSEMBL_URL}/genome/{self.genome_tag}"},
        )
        mock_species_lookup.assert_called_once_with("Homo_sapiens")
        self.mock_genome_tag_lookup.assert_called_once_with(self.genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_bare_species_path_with_redirect(self, mock_species_lookup):
        """Resolve a bare species path to the new Ensembl species page."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Crocodylus_porosus"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            f"{ENSEMBL_URL}/genome/{self.genome_tag}",
        )
        mock_species_lookup.assert_called_once_with("Crocodylus_porosus")
        self.mock_genome_tag_lookup.assert_called_once_with(self.genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_bare_species_path_without_uuid_redirects_to_archive(
        self, mock_species_lookup
    ):
        """Redirect bare species paths to archive when no new Ensembl UUID exists."""
        mock_species_lookup.side_effect = SpeciesGenomeUuidNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Homo_sapiens"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://jun2026.archive.ensembl.org/Homo_sapiens",
        )
        mock_species_lookup.assert_called_once_with("Homo_sapiens")

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_gene_summary_with_redirect(self, mock_species_lookup):
        """Resolve a supported gene URL to a permanent new Ensembl redirect."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Summary"
                    "?g=ENSG00000012048"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            (
                f"{ENSEMBL_URL}/feature-explorer/{self.genome_tag}"
                "/gene:ENSG00000012048"
            ),
        )
        self.mock_genome_tag_lookup.assert_called_once_with(self.genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_gene_summary_uses_genome_tag_for_uuid_lookup_value(
        self, mock_species_lookup
    ):
        """Pass mapped UUIDs to metadata and use the returned genome tag."""
        genome_uuid = UUID("12345678-1234-5678-1234-567812345678")
        mock_species_lookup.return_value = genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Summary"
                    "?g=ENSG00000012048"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/feature-explorer/{self.genome_tag}"
                    "/gene:ENSG00000012048"
                )
            },
        )
        self.mock_genome_tag_lookup.assert_called_once_with(genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_gene_summary_without_genome_tag_uses_genome_uuid(
        self, mock_species_lookup
    ):
        """Retain the current genome UUID when metadata has no genome tag."""
        mock_species_lookup.return_value = self.genome_uuid
        self.mock_genome_tag_lookup.return_value = None

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Summary"
                    "?g=ENSG00000012048"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/feature-explorer/{self.genome_uuid}"
                    "/gene:ENSG00000012048"
                )
            },
        )
        self.mock_genome_tag_lookup.assert_called_once_with(self.genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_gene_summary_returns_500_for_genome_tag_lookup_failure(
        self, mock_species_lookup
    ):
        """Return an error when the explain endpoint cannot be queried."""
        mock_species_lookup.return_value = self.genome_uuid
        self.mock_genome_tag_lookup.side_effect = Exception(
            "Failed to fetch genome tag for genome 'genome_uuid1': 503 Server Error"
        )

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Summary"
                    "?g=ENSG00000012048"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to fetch genome tag", response.text)
        self.mock_genome_tag_lookup.assert_called_once_with(self.genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_gene_summary_returns_404_when_genome_metadata_is_missing(
        self, mock_species_lookup
    ):
        """Do not convert a missing metadata genome into a server error."""
        from app.api.utils.metadata import MetadataNotFoundError

        mock_species_lookup.return_value = self.genome_uuid
        self.mock_genome_tag_lookup.side_effect = MetadataNotFoundError(
            f"Genome '{self.genome_uuid}' was not found in the metadata API"
        )

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Summary"
                    "?g=ENSG00000012048"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("was not found in the metadata API", response.text)
        self.mock_genome_tag_lookup.assert_called_once_with(self.genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_location_genome_with_region(self, mock_species_lookup):
        """Resolve Location/Genome URLs with a region to genome browser focus."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://staging.ensembl.org/Mus_musculus/Location/Genome"
                    "?db=core;r=11:101061349-101082747"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/genome-browser/{self.genome_tag}"
                    "?focus=location:11:101061349-101082747"
                    "&location=11:101061349-101082747"
                )
            },
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_location_view_with_semicolon_query(self, mock_species_lookup):
        """Resolve old-style semicolon-delimited query strings."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Location/View"
                    "?db=core;r=17:38449840-38530994"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/genome-browser/{self.genome_tag}"
                    "?focus=location:17:38449840-38530994"
                    "&location=17:38449840-38530994"
                )
            },
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_location_view_with_transcript_focus(self, mock_species_lookup):
        """Resolve Location/View transcript URLs to genome browser focus."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Location/View"
                    "?t=ENST00000357654"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/genome-browser/{self.genome_tag}"
                    "?focus=transcript:ENST00000357654"
                )
            },
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_gene_feature_explorer_pages(self, mock_species_lookup):
        """Resolve supported gene pages to the new Ensembl feature explorer."""
        mock_species_lookup.return_value = self.genome_uuid

        for page in ("Sequence", "Expression"):
            with self.subTest(page=page):
                response = self.client.get(
                    self.mock_url_resolver_api_url,
                    params={
                        "url": (
                            f"https://www.ensembl.org/Homo_sapiens/Gene/{page}"
                            "?g=ENSG00000012048"
                        )
                    },
                    headers={"accept": "application/json"},
                    follow_redirects=False,
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json(),
                    {
                        "resolved_url": (
                            f"{ENSEMBL_URL}/feature-explorer/{self.genome_tag}"
                            "/gene:ENSG00000012048"
                        )
                    },
                )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_transcript_summary(self, mock_species_lookup):
        """Resolve a transcript summary URL to the new Ensembl feature explorer."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Transcript/Summary"
                    "?t=ENST00000357654"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/feature-explorer/{self.genome_tag}"
                    "/transcript:ENST00000357654"
                )
            },
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_transcript_sequence(self, mock_species_lookup):
        """Resolve transcript sequence URLs to the new Ensembl feature explorer."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Transcript/Sequence"
                    "?t=ENST00000357654"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/feature-explorer/{self.genome_tag}"
                    "/transcript:ENST00000357654"
                )
            },
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_variation_explore(self, mock_species_lookup):
        """Resolve a legacy variant URL through the variant search API."""
        mock_species_lookup.return_value = self.genome_uuid
        self.mock_variant_search.return_value = {
            "variant_name": "rs99",
            "genome_id": self.genome_uuid,
            "region_name": "7",
            "start": 24399036,
        }

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Variation/Explore"
                    "?foo=bar;v=rs99;r=ignored"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/feature-explorer/{self.genome_tag}"
                    "/variant:7:24399036:rs99?allele=0"
                )
            },
        )
        mock_species_lookup.assert_called_once_with("Homo_sapiens")
        self.mock_variant_search.assert_called_once_with(self.genome_uuid, "rs99")
        self.mock_genome_tag_lookup.assert_called_once_with(self.genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_variation_mappings(self, mock_species_lookup):
        """Resolve mappings pages with transcript consequences selected."""
        mock_species_lookup.return_value = self.genome_uuid
        self.mock_variant_search.return_value = {
            "variant_name": "rs99",
            "genome_id": self.genome_uuid,
            "region_name": "7",
            "start": 24399036,
        }

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://www.ensembl.org/Homo_sapiens/Variation/Mappings?v=rs99"
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/feature-explorer/{self.genome_tag}"
                    "/variant:7:24399036:rs99?allele=0&view=transcript-consequences"
                )
            },
        )
        self.mock_variant_search.assert_called_once_with(self.genome_uuid, "rs99")
        self.mock_genome_tag_lookup.assert_called_once_with(self.genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_variation_population(self, mock_species_lookup):
        """Resolve population pages with allele frequencies selected."""
        mock_species_lookup.return_value = self.genome_uuid
        self.mock_variant_search.return_value = {
            "variant_name": "rs99",
            "genome_id": self.genome_uuid,
            "region_name": "7",
            "start": 24399036,
        }

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://www.ensembl.org/Homo_sapiens/Variation/Population?v=rs99"
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "resolved_url": (
                    f"{ENSEMBL_URL}/feature-explorer/{self.genome_tag}"
                    "/variant:7:24399036:rs99?allele=0&view=allele-frequencies"
                )
            },
        )
        self.mock_genome_tag_lookup.assert_called_once_with(self.genome_uuid)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_variation_explore_requires_variant_id(self, mock_species_lookup):
        """Return 400 when a variant URL does not provide the ``v`` parameter."""
        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://www.ensembl.org/Homo_sapiens/Variation/Explore?x=1"
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 400)
        mock_species_lookup.assert_not_called()
        self.mock_variant_search.assert_not_called()
        self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_variation_explore_returns_404_when_not_found(
        self, mock_species_lookup
    ):
        """Return 404 when the supplied variant cannot be found in the genome."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://www.ensembl.org/Homo_sapiens/Variation/Explore?v=rs99"
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        self.mock_variant_search.assert_called_once_with(self.genome_uuid, "rs99")
        self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_unresolved_plant_variant_html_redirects_to_plant_archive(
        self, mock_species_lookup
    ):
        """Redirect browser users immediately to the matching division archive."""
        mock_species_lookup.return_value = self.genome_uuid
        legacy_url = (
            "https://plants.ensembl.org/Triticum_aestivum_mattis/Variation/Explore"
            "?db=core;g=TraesCS5B02G111700;r=5D:253902284-253903488;"
            "v=BA00494366;vdb=variation;vf=480705"
        )
        archive_url = (
            "https://eg63-plants.ensembl.org/Triticum_aestivum_mattis/Variation/Explore"
            "?db=core;g=TraesCS5B02G111700;r=5D:253902284-253903488;"
            "v=BA00494366;vdb=variation;vf=480705"
        )

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": legacy_url},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(response.headers["location"], archive_url)
        self.mock_variant_search.assert_called_once_with(
            self.genome_uuid, "BA00494366"
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_missing_required_query_parameter(self, mock_species_lookup):
        """Return 400 when a URL shape is known but its parameter is missing."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Homo_sapiens/Gene/Summary"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 400)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_unsupported_template(self, mock_species_lookup):
        """Return 404 for URL shapes with no supported new Ensembl mapping."""
        mock_species_lookup.return_value = self.genome_uuid

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Variation"
                    "?g=ENSG00000012048"
                )
            },
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        mock_species_lookup.assert_not_called()
        self.mock_genome_tag_lookup.assert_not_called()

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_missing_species_redirects_to_main_archive(
        self, mock_species_lookup
    ):
        """Redirect main-site URLs to the release archive when UUID is missing."""
        mock_species_lookup.side_effect = SpeciesGenomeUuidNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/Homo_sapiens/Info/Index"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://jun2026.archive.ensembl.org/Homo_sapiens/Info/Index",
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_null_species_uuid_redirects_to_main_archive(
        self, mock_species_lookup
    ):
        """Redirect to archive when a species row has no new Ensembl genome UUID."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Gene/Summary"
                    "?g=ENSG00000012048"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://jun2026.archive.ensembl.org/Homo_sapiens/Gene/Summary"
            "?g=ENSG00000012048",
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_missing_species_redirects_to_plants_archive(
        self, mock_species_lookup
    ):
        """Redirect plants URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://plants.ensembl.org/Arabidopsis_thaliana/Info/Index"
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://eg63-plants.ensembl.org/Arabidopsis_thaliana/Info/Index",
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_missing_species_redirects_to_metazoa_archive(
        self, mock_species_lookup
    ):
        """Redirect metazoa URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://metazoa.ensembl.org/Caenorhabditis_elegans/Info/Index"
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://eg63-metazoa.ensembl.org/Caenorhabditis_elegans/Info/Index",
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_missing_species_redirects_to_fungi_archive(
        self, mock_species_lookup
    ):
        """Redirect fungi URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://fungi.ensembl.org/Saccharomyces_cerevisiae/Info/Index"
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://eg63-fungi.ensembl.org/Saccharomyces_cerevisiae/Info/Index",
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_missing_species_redirects_to_protists_archive(
        self, mock_species_lookup
    ):
        """Redirect protists URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": "https://protists.ensembl.org/Plasmodium_falciparum/Info/Index"
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://eg63-protists.ensembl.org/Plasmodium_falciparum/Info/Index",
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_missing_species_redirects_to_bacteria_archive(
        self, mock_species_lookup
    ):
        """Redirect bacteria URLs to the Ensembl Genomes archive host."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://bacteria.ensembl.org/"
                    "Aliiglaciecola_lipolytica_e3_gca_000314975/Info/Index"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            (
                "https://eg63-bacteria.ensembl.org/"
                "Aliiglaciecola_lipolytica_e3_gca_000314975/Info/Index"
            ),
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_missing_species_archive_preserves_query_and_fragment(
        self, mock_species_lookup
    ):
        """Preserve legacy URL query strings and fragments in archive fallback."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={
                "url": (
                    "https://www.ensembl.org/Homo_sapiens/Location/View"
                    "?r=1:1-100#content"
                )
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"],
            "https://jun2026.archive.ensembl.org/Homo_sapiens/Location/View"
            "?r=1:1-100#content",
        )

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_missing_species_unknown_host_does_not_redirect(
        self, mock_species_lookup
    ):
        """Return an error for unknown hosts instead of guessing an archive URL."""
        mock_species_lookup.side_effect = SpeciesNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://example.org/Homo_sapiens/Info/Index"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("location", response.headers)

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_unknown_page_with_json_response(self, mock_species_lookup):
        """Return JSON error for unsupported one-segment legacy paths."""
        mock_species_lookup.side_effect = SpeciesMappingNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/foo"},
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("location", response.headers)
        mock_species_lookup.assert_called_once_with("foo")

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_unknown_page_with_html_redirects_to_archive(
        self, mock_species_lookup
    ):
        """Redirect browser users to the archive for unsupported legacy paths."""
        mock_species_lookup.side_effect = SpeciesMappingNotFoundError("not found")

        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://www.ensembl.org/foo"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"], "https://jun2026.archive.ensembl.org/foo"
        )
        mock_species_lookup.assert_called_once_with("foo")

    @patch(
        "app.api.resources.legacy_url_resolver_view.get_genome_uuid_from_species_url"
    )
    def test_resolve_unknown_stable_id_with_html_redirects_to_archive(
        self, mock_species_lookup
    ):
        """Redirect to the archive stable-ID URL when a legacy ID cannot resolve."""
        response = self.client.get(
            self.mock_url_resolver_api_url,
            params={"url": "https://staging.ensembl.org/id/foo"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 308)
        self.assertEqual(
            response.headers["location"], "https://jun2026.archive.ensembl.org/id/foo"
        )
        self.mock_genome_tag_lookup.assert_not_called()
        mock_species_lookup.assert_not_called()


if __name__ == "__main__":
    unittest.main()

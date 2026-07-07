import unittest

from fastapi.testclient import TestClient

from app.api.models.resolver import RapidResolverResponse
from app.core.config import ENSEMBL_URL, normalize_app_prefix
from app.main import get_application


class TestAppPrefix(unittest.TestCase):
    def test_normalize_app_prefix_defaults_to_root(self):
        self.assertEqual(normalize_app_prefix(""), "/")
        self.assertEqual(normalize_app_prefix("/"), "/")

    def test_normalize_app_prefix_adds_leading_slash_and_removes_trailing_slash(self):
        self.assertEqual(normalize_app_prefix("api/resolver"), "/api/resolver")
        self.assertEqual(normalize_app_prefix("/api/resolver/"), "/api/resolver")

    def test_default_prefix_preserves_existing_routes(self):
        client = TestClient(get_application(app_prefix="/"))

        response = client.get(
            "/rapid/",
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            RapidResolverResponse(resolved_url=ENSEMBL_URL).model_dump(mode="json"),
        )

    def test_configured_prefix_moves_routes(self):
        client = TestClient(get_application(app_prefix="/api/resolver"))

        prefixed_response = client.get(
            "/api/resolver/rapid/",
            headers={"accept": "application/json"},
            follow_redirects=False,
        )
        unprefixed_response = client.get(
            "/rapid/",
            headers={"accept": "application/json"},
            follow_redirects=False,
        )

        self.assertEqual(prefixed_response.status_code, 200)
        self.assertEqual(unprefixed_response.status_code, 404)

    def test_configured_prefix_moves_docs_entrypoint(self):
        client = TestClient(get_application(app_prefix="/api/resolver"))

        prefixed_response = client.get("/api/resolver/", follow_redirects=False)
        unprefixed_response = client.get("/", follow_redirects=False)

        self.assertEqual(prefixed_response.status_code, 200)
        self.assertIn("text/html", prefixed_response.headers["content-type"])
        self.assertEqual(unprefixed_response.status_code, 404)

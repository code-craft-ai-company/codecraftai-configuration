"""
    Unit tests for :class:`GithubConfigSynchronizer` publishing.

    The GitHub REST API is replaced with an in-memory fake that answers each endpoint of the
    publish flow with the status code GitHub documents for it, so the tests verify the endpoints
    the synchronizer calls and the status codes it accepts.
"""

import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure the local package sources and virtual environment dependencies are available
REPO_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_PATHS = [
    REPO_ROOT / "source" / "packages",
    REPO_ROOT / ".venv" / "src",
    REPO_ROOT / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
]
for pkg_path in PACKAGE_PATHS:
    if pkg_path.exists():
        sys.path.insert(0, str(pkg_path))

from ccai.configuration.synchronization import githubconfigsynchronizer
from ccai.configuration.synchronization.githubconfigsynchronizer import GithubConfigSynchronizer
from ccai.errors.exceptions import PublishError


OWNER = "example-owner"
REPO = "example-repo"
API_REPO_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"
COMMIT_URL = f"{API_REPO_URL}/git/commits/commit-sha-1"
TREE_URL = f"{API_REPO_URL}/git/trees/tree-sha-1"
REF_READ_URL = f"{API_REPO_URL}/git/ref/heads/main"
REF_UPDATE_URL = f"{API_REPO_URL}/git/refs/heads/main"


class FakeResponse:
    """
        A minimal stand-in for :class:`requests.Response`.
    """

    def __init__(self, status_code: int, body: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self._body = body
        return

    def json(self) -> Optional[Dict[str, Any]]:
        body = self._body
        return body


class FakeGithubApi:
    """
        A fake for the ``requests`` module that answers the GitHub git-data endpoints used by the
        publish flow with their documented status codes.  Unknown requests are answered with 404.
    """

    Response = FakeResponse

    def __init__(self):
        self.calls: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []
        self.routes: Dict[Tuple[str, str], FakeResponse] = {
            ("GET", REF_READ_URL): FakeResponse(200, {"object": {"url": COMMIT_URL}}),
            ("GET", COMMIT_URL): FakeResponse(200, {"sha": "commit-sha-1", "tree": {"sha": "tree-sha-1", "url": TREE_URL}}),
            ("POST", f"{API_REPO_URL}/git/blobs"): FakeResponse(201, {"sha": "blob-sha-1", "url": f"{API_REPO_URL}/git/blobs/blob-sha-1"}),
            ("GET", TREE_URL): FakeResponse(200, {"sha": "tree-sha-1"}),
            ("POST", f"{API_REPO_URL}/git/trees"): FakeResponse(201, {"sha": "tree-sha-2"}),
            ("POST", f"{API_REPO_URL}/git/commits"): FakeResponse(201, {"sha": "commit-sha-2"}),
            ("PATCH", REF_UPDATE_URL): FakeResponse(200, {"ref": "refs/heads/main", "object": {"sha": "commit-sha-2"}}),
        }
        return

    def _answer(self, method: str, url: str, json_body: Optional[Dict[str, Any]]) -> FakeResponse:
        self.calls.append((method, url, json_body))
        route_key = (method, url)
        if route_key in self.routes:
            resp = self.routes[route_key]
        else:
            resp = FakeResponse(404, {"message": "Not Found"})
        return resp

    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> FakeResponse:
        resp = self._answer("GET", url, None)
        return resp

    def post(self, url: str, headers: Optional[Dict[str, str]] = None, json: Optional[Dict[str, Any]] = None) -> FakeResponse:
        resp = self._answer("POST", url, json)
        return resp

    def patch(self, url: str, headers: Optional[Dict[str, str]] = None, json: Optional[Dict[str, Any]] = None) -> FakeResponse:
        resp = self._answer("PATCH", url, json)
        return resp


class TestGithubConfigSynchronizerPublish(unittest.TestCase):

    def setUp(self):
        self.fake_api = FakeGithubApi()
        self.original_requests = githubconfigsynchronizer.requests
        githubconfigsynchronizer.requests = self.fake_api

        self.synchronizer = GithubConfigSynchronizer.parse(f"github://{OWNER}/{REPO}/configs")
        self.credentials = {OWNER: ("publisher", "token-value")}
        return

    def tearDown(self):
        githubconfigsynchronizer.requests = self.original_requests
        return

    def _publish(self) -> None:
        self.synchronizer._publish_configuration("venue-a", "user-a", "landscapes", "lab", "json",
                                                 {"a": 1}, credentials=self.credentials)
        return

    def test_publish_completes_with_github_status_codes(self):
        self._publish()

        methods_called = [method for method, _, _ in self.fake_api.calls]
        self.assertEqual(methods_called, ["GET", "GET", "POST", "GET", "POST", "POST", "PATCH"])
        return

    def test_publish_updates_ref_through_refs_endpoint(self):
        self._publish()

        method, url, json_body = self.fake_api.calls[-1]
        self.assertEqual(method, "PATCH")
        self.assertEqual(url, REF_UPDATE_URL)
        self.assertEqual(json_body, {"sha": "commit-sha-2", "force": False})
        return

    def test_publish_raises_when_blob_is_not_created(self):
        self.fake_api.routes[("POST", f"{API_REPO_URL}/git/blobs")] = FakeResponse(422, {"message": "Unprocessable"})

        with self.assertRaises(PublishError):
            self._publish()
        return

    def test_publish_raises_when_ref_update_fails(self):
        self.fake_api.routes[("PATCH", REF_UPDATE_URL)] = FakeResponse(422, {"message": "Update is not a fast forward"})

        with self.assertRaises(PublishError):
            self._publish()
        return


if __name__ == '__main__':
    unittest.main()

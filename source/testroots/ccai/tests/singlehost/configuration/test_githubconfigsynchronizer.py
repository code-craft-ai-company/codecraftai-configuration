"""
    Testbase conversion of the GitHub configuration synchronizer unittest module.

    Verifies that :class:`GithubConfigSynchronizer` publishing calls the GitHub git-data
    endpoints the REST API documents and accepts the status codes GitHub returns for them, and
    that retrieval reads a configuration from the same branch and repository path that
    publishing commits it to.

    Each test replaces the ``requests`` module used by the synchronizer with an in-memory fake
    of the GitHub REST API and restores the original module on completion.
"""

import base64
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure the local package sources and virtual environment dependencies are available
REPO_ROOT = Path(__file__).resolve().parents[6]
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
EXPECTED_PUBLISH_PATH = "configs/venue-a/user-a/landscapes/lab.json"


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


def _contents_url(repository_path: str) -> str:
    """
        Returns the GitHub contents API URL for a file on the ``main`` branch of the fake repository.

        :param repository_path: The repository relative path of the file.

        :returns: The contents API URL.
    """
    url = f"{API_REPO_URL}/contents/{repository_path}?ref=main"
    return url


def _contents_response(content: str) -> FakeResponse:
    """
        Returns a contents API response for a file with the specified text content.

        :param content: The text content of the file.

        :returns: A fake response carrying the base64 encoded content.
    """
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
    resp = FakeResponse(200, {"type": "file", "encoding": "base64", "content": encoded_content})
    return resp


def _create_synchronizer() -> GithubConfigSynchronizer:
    """
        Creates a synchronizer for the fake repository with a 'configs' leaf.

        :returns: The synchronizer.
    """
    synchronizer = GithubConfigSynchronizer.parse(f"github://{OWNER}/{REPO}/configs")
    return synchronizer


def _establish_env() -> Tuple[FakeGithubApi, Any]:
    """
        Establish the per-test environment by replacing the ``requests`` module used by the
        synchronizer with a fake GitHub API.

        :returns: The fake GitHub API and the original ``requests`` module to restore.
    """
    fake_api = FakeGithubApi()
    original_requests = githubconfigsynchronizer.requests
    githubconfigsynchronizer.requests = fake_api
    return fake_api, original_requests


def _cleanup_env(original_requests: Any) -> None:
    """
        Tear down the per-test environment by restoring the original ``requests`` module.

        :param original_requests: The ``requests`` module to restore.
    """
    githubconfigsynchronizer.requests = original_requests
    return


def _publish() -> None:
    """
        Publishes a small JSON configuration through a synchronizer for the fake repository.
    """
    synchronizer = GithubConfigSynchronizer.parse(f"github://{OWNER}/{REPO}/configs")
    credentials = {OWNER: ("publisher", "token-value")}
    synchronizer._publish_configuration("venue-a", "user-a", "landscapes", "lab", "json",
                                        {"a": 1}, credentials=credentials)
    return


def test_publish_completes_with_github_status_codes() -> None:
    """
        Verify that publishing completes when GitHub answers each step with its documented
        status code (blobs/trees/commits 201, ref update 200).
    """
    fake_api, original_requests = _establish_env()
    try:
        _publish()

        methods_called = [method for method, _, _ in fake_api.calls]
        assert methods_called == ["GET", "GET", "POST", "GET", "POST", "POST", "PATCH"]
    finally:
        _cleanup_env(original_requests)
    return


def test_publish_updates_ref_through_refs_endpoint() -> None:
    """
        Verify that the branch head is moved with a PATCH to the plural ``git/refs`` endpoint.
    """
    fake_api, original_requests = _establish_env()
    try:
        _publish()

        method, url, json_body = fake_api.calls[-1]
        assert method == "PATCH"
        assert url == REF_UPDATE_URL
        assert json_body == {"sha": "commit-sha-2", "force": False}
    finally:
        _cleanup_env(original_requests)
    return


def test_publish_raises_when_blob_is_not_created() -> None:
    """
        Verify that a failed blob creation is reported with a :class:`PublishError`.
    """
    fake_api, original_requests = _establish_env()
    try:
        fake_api.routes[("POST", f"{API_REPO_URL}/git/blobs")] = FakeResponse(422, {"message": "Unprocessable"})

        raised = False
        try:
            _publish()
        except PublishError:
            raised = True

        assert raised, "Expected a PublishError when the blob is not created."
    finally:
        _cleanup_env(original_requests)
    return


def test_publish_raises_when_ref_update_fails() -> None:
    """
        Verify that a failed branch head update is reported with a :class:`PublishError`.
    """
    fake_api, original_requests = _establish_env()
    try:
        fake_api.routes[("PATCH", REF_UPDATE_URL)] = FakeResponse(422, {"message": "Update is not a fast forward"})

        raised = False
        try:
            _publish()
        except PublishError:
            raised = True

        assert raised, "Expected a PublishError when the ref update fails."
    finally:
        _cleanup_env(original_requests)
    return


def test_publish_tree_entry_path_is_relative_to_leaf() -> None:
    """
        Verify that the git tree entry path is relative to the repository root, starts with the
        storage-uri leaf and does not start with a '/', which GitHub rejects.
    """
    fake_api, original_requests = _establish_env()
    try:
        _publish()

        tree_calls = [body for method, url, body in fake_api.calls if method == "POST" and url == f"{API_REPO_URL}/git/trees"]
        assert len(tree_calls) == 1

        tree_body = tree_calls[0]
        tree_entry = tree_body["tree"][0]
        assert tree_entry["path"] == EXPECTED_PUBLISH_PATH, f"Unexpected tree entry path: {tree_entry['path']}"
        assert not tree_entry["path"].startswith("/")
    finally:
        _cleanup_env(original_requests)
    return


def test_publish_commit_has_meaningful_message() -> None:
    """
        Verify that the publish commit carries a message naming the configuration and its path.
    """
    fake_api, original_requests = _establish_env()
    try:
        _publish()

        commit_calls = [body for method, url, body in fake_api.calls if method == "POST" and url == f"{API_REPO_URL}/git/commits"]
        assert len(commit_calls) == 1

        commit_message = commit_calls[0]["message"]
        assert "landscapes" in commit_message, f"Unexpected commit message: {commit_message}"
        assert "'lab'" in commit_message, f"Unexpected commit message: {commit_message}"
        assert EXPECTED_PUBLISH_PATH in commit_message, f"Unexpected commit message: {commit_message}"
    finally:
        _cleanup_env(original_requests)
    return


def test_retrieve_returns_published_configuration() -> None:
    """
        Verify that a published configuration is retrieved from the branch and path it was committed to.
    """
    fake_api, original_requests = _establish_env()
    try:
        _publish()

        blob_bodies = [body for method, url, body in fake_api.calls if method == "POST" and url == f"{API_REPO_URL}/git/blobs"]
        tree_bodies = [body for method, url, body in fake_api.calls if method == "POST" and url == f"{API_REPO_URL}/git/trees"]
        blob_body = blob_bodies[0]
        tree_body = tree_bodies[0]
        published_path = tree_body["tree"][0]["path"]
        published_content = base64.b64decode(blob_body["content"]).decode("utf-8")

        # The fake repository now holds the published blob at the committed path on 'main'.
        fake_api.routes[("GET", _contents_url(published_path))] = _contents_response(published_content)

        synchronizer = _create_synchronizer()
        credentials = {OWNER: ("publisher", "token-value")}
        config_format, config_info = synchronizer._retrieve_configuration("venue-a", "user-a", "landscapes", "lab",
                                                                          credentials=credentials)
        assert config_format == "json", f"Unexpected format: {config_format}"
        assert config_info == {"a": 1}, f"Unexpected config: {config_info}"
    finally:
        _cleanup_env(original_requests)
    return


def test_retrieve_prefers_yaml_configuration() -> None:
    """
        Verify that retrieval looks for the YAML form of a configuration first.
    """
    fake_api, original_requests = _establish_env()
    try:
        yaml_path = "configs/venue-a/user-a/topologies/lab.yaml"
        fake_api.routes[("GET", _contents_url(yaml_path))] = _contents_response("b: 2\n")

        synchronizer = _create_synchronizer()
        credentials = {OWNER: ("publisher", "token-value")}
        config_format, config_info = synchronizer._retrieve_configuration("venue-a", "user-a", "topologies", "lab",
                                                                          credentials=credentials)
        assert config_format == "yaml", f"Unexpected format: {config_format}"
        assert config_info == {"b": 2}, f"Unexpected config: {config_info}"

        method, url, _ = fake_api.calls[0]
        assert method == "GET"
        assert url == _contents_url(yaml_path), f"Unexpected url: {url}"
    finally:
        _cleanup_env(original_requests)
    return


def test_retrieve_returns_none_when_configuration_is_missing() -> None:
    """
        Verify that retrieval returns ``(None, None)`` when neither form of the configuration exists.
    """
    fake_api, original_requests = _establish_env()
    try:
        synchronizer = _create_synchronizer()
        credentials = {OWNER: ("publisher", "token-value")}
        config_format, config_info = synchronizer._retrieve_configuration("venue-a", "user-a", "landscapes", "lab",
                                                                          credentials=credentials)
        assert config_format is None
        assert config_info is None

        urls_called = [url for _, url, _ in fake_api.calls]
        expected_urls = [_contents_url("configs/venue-a/user-a/landscapes/lab.yaml"),
                         _contents_url("configs/venue-a/user-a/landscapes/lab.json")]
        assert urls_called == expected_urls, f"Unexpected urls: {urls_called}"
    finally:
        _cleanup_env(original_requests)
    return


def test_retrieve_raises_on_unexpected_status() -> None:
    """
        Verify that retrieval reports a status other than 200 or 404 instead of treating it as missing.
    """
    fake_api, original_requests = _establish_env()
    try:
        yaml_path = "configs/venue-a/user-a/landscapes/lab.yaml"
        fake_api.routes[("GET", _contents_url(yaml_path))] = FakeResponse(401, {"message": "Bad credentials"})

        synchronizer = _create_synchronizer()
        credentials = {OWNER: ("publisher", "token-value")}

        raised = False
        try:
            synchronizer._retrieve_configuration("venue-a", "user-a", "landscapes", "lab", credentials=credentials)
        except RuntimeError:
            raised = True

        assert raised, "Expected a RuntimeError when GitHub answers with an unexpected status."
    finally:
        _cleanup_env(original_requests)
    return


def test_try_retrieve_saves_published_configuration_locally() -> None:
    """
        Verify that ``try_retrieve`` saves a configuration found on the branch into the local store.
    """
    fake_api, original_requests = _establish_env()
    try:
        json_path = "configs/venue-a/user-a/runtimes/lab.json"
        fake_api.routes[("GET", _contents_url(json_path))] = _contents_response(json.dumps({"c": 3}))

        synchronizer = _create_synchronizer()
        credentials = {OWNER: ("publisher", "token-value")}

        with tempfile.TemporaryDirectory() as local_store:
            errors = synchronizer.try_retrieve(local_store, "venue-a", "user-a", "lab", credentials=credentials)
            assert errors == [], f"Unexpected errors: {errors}"

            local_file = os.path.join(local_store, "runtimes", "lab.json")
            assert os.path.exists(local_file), f"Expected local file: {local_file}"
            with open(local_file, "r") as lf:
                local_info = json.load(lf)
            assert local_info == {"c": 3}, f"Unexpected config: {local_info}"
    finally:
        _cleanup_env(original_requests)
    return

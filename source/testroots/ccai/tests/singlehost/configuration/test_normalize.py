"""
    Testbase tests for :func:`ccai.configuration.normalize.normalize_source_path_list`.

    Verifies that recognized source-URI schemes (couchdb, http, https, mongodb,
    dir) are preserved verbatim while bare file paths are normalized to absolute
    paths.
"""

import os
import sys

from pathlib import Path

# Ensure the local package sources are available
REPO_ROOT = Path(__file__).resolve().parents[6]
PACKAGE_PATHS = [
    REPO_ROOT / "source" / "packages",
]
for pkg_path in PACKAGE_PATHS:
    if pkg_path.exists():
        sys.path.insert(0, str(pkg_path))

from ccai.configuration.normalize import normalize_source_path_list


def test_couchdb_uri_normalization() -> None:
    """
        Verify that couchdb:// URIs are treated as source URIs and not normalized as file paths.
    """
    uri = "couchdb://http+localhost:5984/mydb"
    result = normalize_source_path_list([uri])
    assert result[0] == uri
    return


def test_other_schemes_normalization() -> None:
    """
        Verify that other supported schemes are also preserved.
    """
    uris = [
        "http://example.com",
        "https://example.com",
        "mongodb://localhost:27017",
        "dir:///tmp/config"
    ]
    result = normalize_source_path_list(uris)
    assert result == uris
    return


def test_file_path_normalization() -> None:
    """
        Verify that file paths are normalized to absolute paths.
    """
    path = "some/local/file"
    result = normalize_source_path_list([path])
    expanded = os.path.expandvars(os.path.expanduser(path))
    expected = os.path.abspath(expanded)
    assert result[0] == expected
    return

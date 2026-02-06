
import unittest
import os
import sys
from pathlib import Path

# Ensure the local package sources are available
REPO_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_PATHS = [
    REPO_ROOT / "source" / "packages",
]
for pkg_path in PACKAGE_PATHS:
    if pkg_path.exists():
        sys.path.insert(0, str(pkg_path))

from automojo.configuration.normalize import normalize_source_path_list

class TestNormalize(unittest.TestCase):
    def test_couchdb_uri_normalization(self):
        """
        Verify that couchdb:// URIs are treated as source URIs and not normalized as file paths.
        """
        uri = "couchdb://http+localhost:5984/mydb"
        result = normalize_source_path_list([uri])
        self.assertEqual(result[0], uri)

    def test_other_schemes_normalization(self):
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
        self.assertEqual(result, uris)

    def test_file_path_normalization(self):
        """
        Verify that file paths are normalized to absolute paths.
        """
        path = "some/local/file"
        result = normalize_source_path_list([path])
        expected = os.path.abspath(os.path.expandvars(os.path.expanduser(path)))
        self.assertEqual(result[0], expected)

if __name__ == '__main__':
    unittest.main()

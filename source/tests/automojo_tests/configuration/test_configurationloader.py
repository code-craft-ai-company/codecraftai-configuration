import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

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

from automojo.configuration.configurationformat import ConfigurationFormat
from automojo.configuration.configurationloader import ConfigurationLoader
from automojo.configuration.cryptography import (
    create_encrypted_configuration,
    generate_fernet_key,
)
from automojo.errors.exceptions import SemanticError, ConfigurationError


class TestConfigurationLoader(unittest.TestCase):

    def setUp(self):
        self.configDirectory = tempfile.mkdtemp("config-tests")
        return

    def tearDown(self):
        if os.path.exists(self.configDirectory):
            shutil.rmtree(self.configDirectory, ignore_errors=True)
        return

    def test_load_json_configuration_by_fullfile(self):

        json_file = os.path.join(self.configDirectory, 'fullfile-conf.json')
        with open(json_file, 'w') as f:
            f.write('{"b": 2}')

        loader = ConfigurationLoader([])
        data_json = loader.load_configuration_from_file(json_file)
        self.assertEqual(data_json['b'], 2)
        return


    def test_load_json_configuration_by_name(self):

        json_file = os.path.join(self.configDirectory, 'nameonly-conf.json')
        with open(json_file, 'w') as f:
            f.write('{"b": 2}')

        loader = ConfigurationLoader([f'dir://{self.configDirectory}'])
        config_url, data_json = loader.load_configuration_by_name("nameonly-conf")
        self.assertEqual(data_json['b'], 2)

        return


    def test_load_yaml_configuration_by_fullfile(self):

        yaml_file = os.path.join(self.configDirectory, 'nameonly-conf.yaml')
        with open(yaml_file, 'w') as f:
            f.write('a: 1\n')

        loader = ConfigurationLoader([])
        data_yaml = loader.load_configuration_from_file(yaml_file)
        self.assertEqual(data_yaml['a'], 1)
        return


    def test_load_yaml_configuration_by_name(self):

        yaml_file = os.path.join(self.configDirectory, 'nameonly-conf.yaml')
        with open(yaml_file, 'w') as f:
            f.write('a: 1\n')

        loader = ConfigurationLoader([f'dir://{self.configDirectory}'])
        config_uri, data_yaml = loader.load_configuration_by_name("nameonly-conf")
        self.assertEqual(data_yaml['a'], 1)

        return

    def test_load_encrypted_configuration_with_keyphrase(self):

        encrypted_payload = {'secret': 'value'}
        plain_json = json.dumps(encrypted_payload)
        keyphrase = "encryption-passphrase"
        key = generate_fernet_key(keyphrase)

        encrypted_doc = create_encrypted_configuration(
            key,
            plain_json,
            format=ConfigurationFormat.JSON
        )

        encrypted_path = os.path.join(self.configDirectory, 'encrypted.json')
        with open(encrypted_path, 'w') as f:
            json.dump(encrypted_doc, f)

        loader = ConfigurationLoader([])
        decrypted_payload = loader.load_configuration_from_file(
            encrypted_path,
            keyphrase=keyphrase
        )

        self.assertEqual(decrypted_payload, encrypted_payload)
        return

    def test_load_configuration_by_name_with_conflicting_keys(self):

        yaml_file = os.path.join(self.configDirectory, 'conflict.yaml')
        with open(yaml_file, 'w') as f:
            f.write('a: 1\n')

        loader = ConfigurationLoader([f'dir://{self.configDirectory}'])

        with self.assertRaises(SemanticError):
            loader.load_configuration_by_name(
                "conflict",
                key="abc",
                keyphrase="def"
            )
        return

    def test_load_encrypted_configuration_missing_format(self):
        # Create an encrypted config without "format" field
        encrypted_payload = {'secret': 'value'}
        plain_json = json.dumps(encrypted_payload)
        keyphrase = "encryption-passphrase"
        key = generate_fernet_key(keyphrase)

        # Manually create encrypted doc without format
        encrypted_content = create_encrypted_configuration(
            key,
            plain_json,
            format=ConfigurationFormat.JSON
        )["encrypted_content"]

        encrypted_doc = {
            "encrypted_content": encrypted_content
            # Missing "format"
        }

        encrypted_path = os.path.join(self.configDirectory, 'encrypted_no_format.json')
        with open(encrypted_path, 'w') as f:
            json.dump(encrypted_doc, f)

        loader = ConfigurationLoader([])

        # It should raise ConfigurationError because format is unknown
        with self.assertRaises(ConfigurationError) as cm:
            loader.load_configuration_from_file(
                encrypted_path,
                keyphrase=keyphrase
            )

        self.assertIn("UnExpected error parsing decrypted configuration content.  Un-supported format.", str(cm.exception))
        return

if __name__ == '__main__':
    unittest.main()

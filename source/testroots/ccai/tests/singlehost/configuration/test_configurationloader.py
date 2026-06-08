"""
    Testbase conversion of the configuration loader unittest module.

    Verifies the behaviour of :class:`ConfigurationLoader` for loading JSON and
    YAML configuration documents by full file path and by name, decrypting
    encrypted configuration documents with a keyphrase, and surfacing the
    appropriate errors for conflicting key arguments and unknown formats.

    Each test establishes its own temporary configuration directory for
    isolation and removes that directory on completion.
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

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

from ccai.configuration.configurationformat import ConfigurationFormat
from ccai.configuration.configurationloader import ConfigurationLoader
from ccai.configuration.cryptography import (
    create_encrypted_configuration,
    generate_fernet_key,
)
from ccai.errors.exceptions import SemanticError, ConfigurationError


def _establish_env() -> str:
    """
        Establish the per-test environment by creating a temporary
        configuration directory.

        :returns: The path to the temporary configuration directory.
    """
    config_directory = tempfile.mkdtemp("config-tests")
    return config_directory


def _cleanup_env(config_directory: str) -> None:
    """
        Tear down the per-test environment by removing the temporary
        configuration directory if it still exists.

        :param config_directory: The path to the temporary configuration
            directory to remove.
    """
    if os.path.exists(config_directory):
        shutil.rmtree(config_directory, ignore_errors=True)
    return


def test_load_json_configuration_by_fullfile() -> None:
    """
        Verify that a JSON configuration document can be loaded by its full
        file path.
    """
    config_directory = _establish_env()
    try:
        json_file = os.path.join(config_directory, 'fullfile-conf.json')
        with open(json_file, 'w') as f:
            f.write('{"b": 2}')

        loader = ConfigurationLoader([])
        data_json = loader.load_configuration_from_file(json_file)
        assert data_json['b'] == 2
    finally:
        _cleanup_env(config_directory)
    return


def test_load_json_configuration_by_name() -> None:
    """
        Verify that a JSON configuration document can be loaded by name from a
        configured directory search location.
    """
    config_directory = _establish_env()
    try:
        json_file = os.path.join(config_directory, 'nameonly-conf.json')
        with open(json_file, 'w') as f:
            f.write('{"b": 2}')

        loader = ConfigurationLoader([f'dir://{config_directory}'])
        config_url, data_json = loader.load_configuration_by_name("nameonly-conf")
        assert data_json['b'] == 2
    finally:
        _cleanup_env(config_directory)
    return


def test_load_yaml_configuration_by_fullfile() -> None:
    """
        Verify that a YAML configuration document can be loaded by its full
        file path.
    """
    config_directory = _establish_env()
    try:
        yaml_file = os.path.join(config_directory, 'nameonly-conf.yaml')
        with open(yaml_file, 'w') as f:
            f.write('a: 1\n')

        loader = ConfigurationLoader([])
        data_yaml = loader.load_configuration_from_file(yaml_file)
        assert data_yaml['a'] == 1
    finally:
        _cleanup_env(config_directory)
    return


def test_load_yaml_configuration_by_name() -> None:
    """
        Verify that a YAML configuration document can be loaded by name from a
        configured directory search location.
    """
    config_directory = _establish_env()
    try:
        yaml_file = os.path.join(config_directory, 'nameonly-conf.yaml')
        with open(yaml_file, 'w') as f:
            f.write('a: 1\n')

        loader = ConfigurationLoader([f'dir://{config_directory}'])
        config_uri, data_yaml = loader.load_configuration_by_name("nameonly-conf")
        assert data_yaml['a'] == 1
    finally:
        _cleanup_env(config_directory)
    return


def test_load_encrypted_configuration_with_keyphrase() -> None:
    """
        Verify that an encrypted JSON configuration document can be decrypted
        and loaded using a keyphrase.
    """
    config_directory = _establish_env()
    try:
        encrypted_payload = {'secret': 'value'}
        plain_json = json.dumps(encrypted_payload)
        keyphrase = "encryption-passphrase"
        key = generate_fernet_key(keyphrase)

        encrypted_doc = create_encrypted_configuration(
            key,
            plain_json,
            format=ConfigurationFormat.JSON
        )

        encrypted_path = os.path.join(config_directory, 'encrypted.json')
        with open(encrypted_path, 'w') as f:
            json.dump(encrypted_doc, f)

        loader = ConfigurationLoader([])
        decrypted_payload = loader.load_configuration_from_file(
            encrypted_path,
            keyphrase=keyphrase
        )

        assert decrypted_payload == encrypted_payload
    finally:
        _cleanup_env(config_directory)
    return


def test_load_configuration_by_name_with_conflicting_keys() -> None:
    """
        Verify that supplying both a key and a keyphrase when loading a
        configuration by name raises a :class:`SemanticError`.
    """
    config_directory = _establish_env()
    try:
        yaml_file = os.path.join(config_directory, 'conflict.yaml')
        with open(yaml_file, 'w') as f:
            f.write('a: 1\n')

        loader = ConfigurationLoader([f'dir://{config_directory}'])

        raised = False
        try:
            loader.load_configuration_by_name(
                "conflict",
                key="abc",
                keyphrase="def"
            )
        except SemanticError:
            raised = True
        assert raised
    finally:
        _cleanup_env(config_directory)
    return


def test_load_encrypted_configuration_missing_format() -> None:
    """
        Verify that loading an encrypted configuration document with a missing
        format field raises a :class:`ConfigurationError` describing the
        unsupported format.
    """
    config_directory = _establish_env()
    try:
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

        encrypted_path = os.path.join(config_directory, 'encrypted_no_format.json')
        with open(encrypted_path, 'w') as f:
            json.dump(encrypted_doc, f)

        loader = ConfigurationLoader([])

        # It should raise ConfigurationError because format is unknown
        raised = False
        caught_exception = None
        try:
            loader.load_configuration_from_file(
                encrypted_path,
                keyphrase=keyphrase
            )
        except ConfigurationError as cm:
            raised = True
            caught_exception = cm
        assert raised

        assert "UnExpected error parsing decrypted configuration content.  Un-supported format." in str(caught_exception)
    finally:
        _cleanup_env(config_directory)
    return

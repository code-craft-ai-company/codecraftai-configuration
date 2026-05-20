"""
.. module:: test_vpnconfigschema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the ``vpn:`` top-level schema fragment.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os
import sys
import unittest

from pathlib import Path
from typing import List, Optional


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


from automojo.errors.exceptions import ConfigurationError

from automojo.configuration.configurationloader import (
    TOP_LEVEL_SCHEMA_LOADERS,
    ConfigurationLoader,
)
from automojo.configuration.schemas.vpnconfigschema import (
    AddressPlane,
    PROVIDER_CATEGORY_COMPATIBILITY,
    VPNBlock,
    VPNOverlayProfile,
    dump_vpn_block,
    load_vpn_block,
)


class FakeCredential:
    """
        Minimal stand-in for the upstream ``BaseCredential`` exposing
        only the ``categories`` attribute that the schema inspects.
    """

    def __init__(self, *, identifier: str, categories: List[str]) -> None:
        self._identifier = identifier
        self._categories = categories
        return

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def categories(self) -> List[str]:
        return self._categories


def make_lookup(creds: dict):
    """
        Builds an injectable credential-lookup callable that returns a
        ``FakeCredential`` for known identifiers and ``None`` otherwise.
    """
    def _lookup(identifier: str) -> Optional[FakeCredential]:
        rtnval = creds.get(identifier)
        return rtnval
    return _lookup


VALID_TAILSCALE_LOOKUP = make_lookup({
    "ts-prov-oauth": FakeCredential(
        identifier="ts-prov-oauth",
        categories=["tailscale-oauth"],
    ),
    "ts-authkey": FakeCredential(
        identifier="ts-authkey",
        categories=["tailscale-authkey"],
    ),
    "tg-sa": FakeCredential(
        identifier="tg-sa",
        categories=["twingate-service-account"],
    ),
})


def make_valid_provider_entry() -> dict:
    rtnval = {
        "name": "lab-tailnet",
        "provider": "tailscale",
        "network": "acme.ts.net",
        "credential_ref": "ts-prov-oauth",
        "tags": ["tag:lab"],
        "dns_suffix": None,
        "magic_dns_enabled": True,
        "acl_ref": None,
    }
    return rtnval


class TestVPNConfigSchema(unittest.TestCase):

    def test_no_block_yields_default_vpnblock(self):
        block = load_vpn_block(data=None)
        self.assertEqual(block.default_plane, AddressPlane.PUBLIC)
        self.assertEqual(len(block.providers), 0)
        return

    def test_empty_block_yields_default_vpnblock(self):
        block = load_vpn_block(data={})
        self.assertEqual(block.default_plane, AddressPlane.PUBLIC)
        self.assertEqual(len(block.providers), 0)
        return

    def test_happy_path_parses_into_typed_block(self):
        data = {
            "default_plane": "OVERLAY",
            "providers": [make_valid_provider_entry()],
        }
        block = load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)

        self.assertEqual(block.default_plane, AddressPlane.OVERLAY)
        self.assertEqual(len(block.providers), 1)

        profile = block.providers[0]
        self.assertIsInstance(profile, VPNOverlayProfile)
        self.assertEqual(profile.name, "lab-tailnet")
        self.assertEqual(profile.provider, "tailscale")
        self.assertEqual(profile.network, "acme.ts.net")
        self.assertEqual(profile.tags, ["tag:lab"])
        self.assertTrue(profile.magic_dns_enabled)
        return

    def test_missing_provider_key_raises_with_key_list(self):
        entry = make_valid_provider_entry()
        del entry["network"]
        data = {"providers": [entry]}

        with self.assertRaises(ConfigurationError) as ctx:
            load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)

        message = str(ctx.exception)
        self.assertIn("missing required keys", message)
        self.assertIn("network", message)
        return

    def test_unknown_provider_raises_with_supported_list(self):
        entry = make_valid_provider_entry()
        entry["provider"] = "meraki"
        data = {"providers": [entry]}

        with self.assertRaises(ConfigurationError) as ctx:
            load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)

        message = str(ctx.exception)
        self.assertIn("tailscale", message)
        self.assertIn("twingate", message)
        self.assertIn("meraki", message)
        return

    def test_bad_default_plane_raises_with_accepted_list(self):
        data = {"default_plane": "WAN"}

        with self.assertRaises(ConfigurationError) as ctx:
            load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)

        message = str(ctx.exception)
        self.assertIn("PUBLIC", message)
        self.assertIn("PRIVATE", message)
        self.assertIn("OVERLAY", message)
        return

    def test_overlay_default_with_no_providers_raises(self):
        data = {"default_plane": "OVERLAY", "providers": []}

        with self.assertRaises(ConfigurationError) as ctx:
            load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)

        message = str(ctx.exception)
        self.assertIn("OVERLAY", message)
        self.assertIn("providers", message)
        return

    def test_unresolved_credential_ref_raises_with_identifier(self):
        entry = make_valid_provider_entry()
        entry["credential_ref"] = "no-such-cred"
        data = {"providers": [entry]}

        with self.assertRaises(ConfigurationError) as ctx:
            load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)

        message = str(ctx.exception)
        self.assertIn("no-such-cred", message)
        return

    def test_credential_category_mismatch_raises(self):
        # Tailscale provider, but referencing a Twingate credential.
        entry = make_valid_provider_entry()
        entry["credential_ref"] = "tg-sa"
        data = {"providers": [entry]}

        with self.assertRaises(ConfigurationError) as ctx:
            load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)

        message = str(ctx.exception)
        self.assertIn("tg-sa", message)
        self.assertIn("twingate-service-account", message)
        self.assertIn("tailscale-oauth", message)
        return

    def test_multi_error_accumulation_lists_each_failure(self):
        # Two simultaneous failures: bad default_plane AND unknown provider.
        entry = make_valid_provider_entry()
        entry["provider"] = "meraki"
        data = {
            "default_plane": "WAN",
            "providers": [entry],
        }

        with self.assertRaises(ConfigurationError) as ctx:
            load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)

        message = str(ctx.exception)
        lines = message.split(os.linesep)
        # Header + one bullet per error.
        bullets = [ln for ln in lines if ln.strip().startswith("- ")]
        self.assertGreaterEqual(len(bullets), 2)
        self.assertIn("default_plane", message)
        self.assertIn("provider", message)
        return

    def test_dump_round_trip_excludes_credential_ref(self):
        entry = make_valid_provider_entry()
        data = {
            "default_plane": "PUBLIC",
            "providers": [entry],
        }

        block = load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)
        dumped = dump_vpn_block(block=block)

        self.assertEqual(dumped["default_plane"], "PUBLIC")
        self.assertEqual(len(dumped["providers"]), 1)
        dumped_entry = dumped["providers"][0]
        self.assertNotIn("credential_ref", dumped_entry)
        self.assertEqual(dumped_entry["name"], "lab-tailnet")
        self.assertEqual(dumped_entry["provider"], "tailscale")
        self.assertEqual(dumped_entry["network"], "acme.ts.net")
        self.assertEqual(dumped_entry["tags"], ["tag:lab"])
        return

    def test_loader_registers_top_level_vpn_key(self):
        self.assertIn("vpn", TOP_LEVEL_SCHEMA_LOADERS)
        self.assertIs(TOP_LEVEL_SCHEMA_LOADERS["vpn"], load_vpn_block)

        loader = ConfigurationLoader([])
        config_info = {
            "vpn": {
                "default_plane": "PRIVATE",
                "providers": [],
            },
            "other": {"unrelated": 1},
        }
        block = loader.load_vpn_block_from_config(config_info)
        self.assertEqual(block.default_plane, AddressPlane.PRIVATE)
        self.assertEqual(len(block.providers), 0)
        return

    def test_loader_returns_default_block_when_no_vpn_key(self):
        loader = ConfigurationLoader([])
        block = loader.load_vpn_block_from_config({"unrelated": 1})
        self.assertEqual(block.default_plane, AddressPlane.PUBLIC)
        self.assertEqual(len(block.providers), 0)
        return

    def test_provider_category_compatibility_table_shape(self):
        # Cheap structural assertion -- protects against accidental edits
        # that would silently widen the accepted credential set.
        self.assertEqual(
            PROVIDER_CATEGORY_COMPATIBILITY["tailscale"],
            {"tailscale-authkey", "tailscale-oauth"},
        )
        self.assertEqual(
            PROVIDER_CATEGORY_COMPATIBILITY["twingate"],
            {"twingate-service-account"},
        )
        return


if __name__ == "__main__":
    unittest.main()

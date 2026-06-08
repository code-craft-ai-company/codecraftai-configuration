"""
.. module:: test_vpnconfigschema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Testbase tests for the ``vpn:`` top-level schema fragment.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os
import sys

from pathlib import Path
from typing import List, Optional


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


from ccai.errors.exceptions import ConfigurationError

from ccai.configuration.configurationloader import (
    TOP_LEVEL_SCHEMA_LOADERS,
    ConfigurationLoader,
)
from ccai.configuration.schemas.vpnconfigschema import (
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


def test_no_block_yields_default_vpnblock() -> None:
    block = load_vpn_block(data=None)
    assert block.default_plane == AddressPlane.PUBLIC
    assert len(block.providers) == 0
    return


def test_empty_block_yields_default_vpnblock() -> None:
    block = load_vpn_block(data={})
    assert block.default_plane == AddressPlane.PUBLIC
    assert len(block.providers) == 0
    return


def test_happy_path_parses_into_typed_block() -> None:
    data = {
        "default_plane": "OVERLAY",
        "providers": [make_valid_provider_entry()],
    }
    block = load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)

    assert block.default_plane == AddressPlane.OVERLAY
    assert len(block.providers) == 1

    profile = block.providers[0]
    assert isinstance(profile, VPNOverlayProfile)
    assert profile.name == "lab-tailnet"
    assert profile.provider == "tailscale"
    assert profile.network == "acme.ts.net"
    assert tuple(profile.tags) == ("tag:lab",)
    assert profile.magic_dns_enabled
    return


def test_missing_provider_key_raises_with_key_list() -> None:
    entry = make_valid_provider_entry()
    del entry["network"]
    data = {"providers": [entry]}

    raised = False
    try:
        load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)
    except ConfigurationError as ctx_exception:
        raised = True
        message = str(ctx_exception)
        assert "missing required keys" in message
        assert "network" in message
    assert raised
    return


def test_unknown_provider_raises_with_supported_list() -> None:
    entry = make_valid_provider_entry()
    entry["provider"] = "meraki"
    data = {"providers": [entry]}

    raised = False
    try:
        load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)
    except ConfigurationError as ctx_exception:
        raised = True
        message = str(ctx_exception)
        assert "tailscale" in message
        assert "twingate" in message
        assert "meraki" in message
    assert raised
    return


def test_bad_default_plane_raises_with_accepted_list() -> None:
    data = {"default_plane": "WAN"}

    raised = False
    try:
        load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)
    except ConfigurationError as ctx_exception:
        raised = True
        message = str(ctx_exception)
        assert "PUBLIC" in message
        assert "PRIVATE" in message
        assert "OVERLAY" in message
    assert raised
    return


def test_overlay_default_with_no_providers_raises() -> None:
    data = {"default_plane": "OVERLAY", "providers": []}

    raised = False
    try:
        load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)
    except ConfigurationError as ctx_exception:
        raised = True
        message = str(ctx_exception)
        assert "OVERLAY" in message
        assert "providers" in message
    assert raised
    return


def test_unresolved_credential_ref_raises_with_identifier() -> None:
    entry = make_valid_provider_entry()
    entry["credential_ref"] = "no-such-cred"
    data = {"providers": [entry]}

    raised = False
    try:
        load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)
    except ConfigurationError as ctx_exception:
        raised = True
        message = str(ctx_exception)
        assert "no-such-cred" in message
    assert raised
    return


def test_credential_category_mismatch_raises() -> None:
    # Tailscale provider, but referencing a Twingate credential.
    entry = make_valid_provider_entry()
    entry["credential_ref"] = "tg-sa"
    data = {"providers": [entry]}

    raised = False
    try:
        load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)
    except ConfigurationError as ctx_exception:
        raised = True
        message = str(ctx_exception)
        assert "tg-sa" in message
        assert "twingate-service-account" in message
        assert "tailscale-oauth" in message
    assert raised
    return


def test_multi_error_accumulation_lists_each_failure() -> None:
    # Two simultaneous failures: bad default_plane AND unknown provider.
    entry = make_valid_provider_entry()
    entry["provider"] = "meraki"
    data = {
        "default_plane": "WAN",
        "providers": [entry],
    }

    raised = False
    try:
        load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)
    except ConfigurationError as ctx_exception:
        raised = True
        message = str(ctx_exception)
        lines = message.split(os.linesep)
        # Header + one bullet per error.
        bullets = [ln for ln in lines if ln.strip().startswith("- ")]
        assert len(bullets) >= 2
        assert "default_plane" in message
        assert "provider" in message
    assert raised
    return


def test_dump_round_trip_excludes_credential_ref() -> None:
    entry = make_valid_provider_entry()
    data = {
        "default_plane": "PUBLIC",
        "providers": [entry],
    }

    block = load_vpn_block(data=data, credential_lookup=VALID_TAILSCALE_LOOKUP)
    dumped = dump_vpn_block(block=block)

    assert dumped["default_plane"] == "PUBLIC"
    assert len(dumped["providers"]) == 1
    dumped_entry = dumped["providers"][0]
    assert "credential_ref" not in dumped_entry
    assert dumped_entry["name"] == "lab-tailnet"
    assert dumped_entry["provider"] == "tailscale"
    assert dumped_entry["network"] == "acme.ts.net"
    assert dumped_entry["tags"] == ["tag:lab"]
    return


def test_loader_registers_top_level_vpn_key() -> None:
    assert "vpn" in TOP_LEVEL_SCHEMA_LOADERS
    assert TOP_LEVEL_SCHEMA_LOADERS["vpn"] is load_vpn_block

    loader = ConfigurationLoader([])
    config_info = {
        "vpn": {
            "default_plane": "PRIVATE",
            "providers": [],
        },
        "other": {"unrelated": 1},
    }
    block = loader.load_vpn_block_from_config(config_info)
    assert block.default_plane == AddressPlane.PRIVATE
    assert len(block.providers) == 0
    return


def test_loader_returns_default_block_when_no_vpn_key() -> None:
    loader = ConfigurationLoader([])
    block = loader.load_vpn_block_from_config({"unrelated": 1})
    assert block.default_plane == AddressPlane.PUBLIC
    assert len(block.providers) == 0
    return


def test_provider_category_compatibility_table_shape() -> None:
    # Cheap structural assertion -- protects against accidental edits
    # that would silently widen the accepted credential set.
    assert PROVIDER_CATEGORY_COMPATIBILITY["tailscale"] == {"tailscale-authkey", "tailscale-oauth"}
    assert PROVIDER_CATEGORY_COMPATIBILITY["twingate"] == {"twingate-service-account"}
    return

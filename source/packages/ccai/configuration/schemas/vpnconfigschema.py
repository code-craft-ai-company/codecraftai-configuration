"""
.. module:: vpnconfigschema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Schema fragment for the top-level ``vpn:`` block of ccai configuration documents.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import os

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ccai.errors.exceptions import ConfigurationError

# ---------------------------------------------------------------------------
# Cross-repository type imports
#
# The canonical definitions of ``AddressPlane`` (codecraftai-interfaces) and
# ``VPNOverlayProfile`` / ``SUPPORTED_VPN_PROVIDERS`` (codecraftai-networking)
# are core dependencies of this package. They are imported hard so that a
# missing or mis-pathed core dependency fails loudly at import time rather
# than silently substituting a structurally divergent local stand-in.
# ---------------------------------------------------------------------------

from ccai.interfaces.addressplane import AddressPlane
from ccai.networking.vpnoverlayprofile import (
    SUPPORTED_VPN_PROVIDERS,
    VPNOverlayProfile,
)


# ---------------------------------------------------------------------------
# Per-provider credential-category compatibility table.
# Sourced from the well-known-vpn-and-venue-categories spec.
# ---------------------------------------------------------------------------

PROVIDER_CATEGORY_COMPATIBILITY: Dict[str, set] = {
    "tailscale": {"tailscale-authkey", "tailscale-oauth"},
    "twingate":  {"twingate-service-account"},
}


@dataclass(frozen=True)
class VPNBlock:
    """
        Typed representation of the ``vpn:`` top-level block.

        :param default_plane: Default address plane used by callers that
            do not specify one. Defaults to ``PUBLIC``.
        :param providers: List of overlay profiles configured for this
            landscape / spec.
    """
    default_plane: AddressPlane = AddressPlane.PUBLIC
    providers: List[VPNOverlayProfile] = field(default_factory=list)


# Type alias for an injected credential-lookup callable. Returning ``None``
# means "credential not found"; returning an object with a ``categories``
# attribute means "found, with these categories". Tests inject a stub;
# production code passes ``None`` to use the well-known singleton.
CredentialLookup = Callable[[str], Optional[Any]]


def load_vpn_block(*, data: Optional[dict] = None,
                   credential_lookup: Optional[CredentialLookup] = None) -> VPNBlock:
    """
        Parses and validates the ``vpn:`` block of a parsed config dict.

        :param data: The dict value of the ``vpn:`` key, or ``None``/``{}``
            when the block is absent.
        :param credential_lookup: Optional callable that resolves a
            credential identifier to a credential object (or ``None`` when
            the identifier is unknown). When omitted and any provider
            entry specifies a ``credential_ref``, this function attempts
            to use ``CredentialManagerSingleton`` from
            ``ccai.credentials.wellknown``.

        :returns: A typed ``VPNBlock``.
        :raises: ConfigurationError accumulating every validation failure.
    """
    block_data: dict = data if data is not None else {}

    err_lines: List[str] = []

    raw_plane = block_data.get("default_plane", "PUBLIC")
    default_plane = _parse_default_plane(raw=raw_plane, err_lines=err_lines)

    providers_raw = block_data.get("providers", [])
    providers: List[VPNOverlayProfile] = []
    if not isinstance(providers_raw, list):
        err_lines.append("vpn.providers must be a list.")
    else:
        resolver = _build_credential_resolver(injected=credential_lookup)
        for idx, entry in enumerate(providers_raw):
            profile = _parse_provider_entry(
                entry=entry,
                idx=idx,
                err_lines=err_lines,
                resolver=resolver,
            )
            if profile is not None:
                providers.append(profile)

    if default_plane == AddressPlane.OVERLAY and len(providers) == 0:
        err_lines.append(
            "vpn.default_plane=OVERLAY requires at least one entry in vpn.providers."
        )

    if len(err_lines) > 0:
        msg_lines = ["vpn-config-schema validation failed:"]
        for line in err_lines:
            msg_lines.append("  - " + line)
        err_msg = os.linesep.join(msg_lines)
        raise ConfigurationError(err_msg)

    rtnval = VPNBlock(default_plane=default_plane, providers=providers)
    return rtnval


def dump_vpn_block(*, block: VPNBlock) -> dict:
    """
        Renders a ``VPNBlock`` back to a plain dict suitable for YAML/JSON
        serialisation.

        Note: ``credential_ref`` is intentionally omitted on every
        ``providers[*]`` entry. Credentials are stored by identifier in
        ``codecraftai-credentials`` and looked up at load time; embedding the
        reference back into the dump would couple two storage layers that
        are deliberately kept independent.

        :param block: The ``VPNBlock`` instance to dump.

        :returns: A dict in the same shape consumed by ``load_vpn_block``,
            minus every ``credential_ref`` field.
    """
    providers_out: List[dict] = []
    for profile in block.providers:
        entry = {
            "name": profile.name,
            "provider": profile.provider,
            "network": profile.network,
            "tags": list(profile.tags),
            "dns_suffix": profile.dns_suffix,
            "magic_dns_enabled": profile.magic_dns_enabled,
            "acl_ref": profile.acl_ref,
        }
        providers_out.append(entry)

    rtnval = {
        "default_plane": block.default_plane.name,
        "providers": providers_out,
    }
    return rtnval


def _parse_default_plane(*, raw: Any, err_lines: List[str]) -> AddressPlane:
    """
        Parses the ``vpn.default_plane`` field, accumulating any error.

        :param raw: The raw value of ``vpn.default_plane`` from the dict.
        :param err_lines: Mutable list of error messages to append to on
            failure.

        :returns: The corresponding ``AddressPlane`` enum member. Returns
            ``AddressPlane.PUBLIC`` as a placeholder when ``raw`` is
            invalid (an error line is also appended in that case).
    """
    rtnval = AddressPlane.PUBLIC

    if not isinstance(raw, str):
        err_lines.append("vpn.default_plane must be a string.")
        return rtnval

    upper = raw.upper()
    if upper == "PUBLIC":
        rtnval = AddressPlane.PUBLIC
    elif upper == "PRIVATE":
        rtnval = AddressPlane.PRIVATE
    elif upper == "OVERLAY":
        rtnval = AddressPlane.OVERLAY
    else:
        err_lines.append(
            f"vpn.default_plane must be one of PUBLIC, PRIVATE, OVERLAY; got {raw!r}."
        )

    return rtnval


def _parse_provider_entry(*, entry: Any, idx: int, err_lines: List[str],
                          resolver: CredentialLookup) -> Optional[VPNOverlayProfile]:
    """
        Validates and constructs a single ``vpn.providers[idx]`` entry.

        :param entry: The raw dict entry for this provider.
        :param idx: The zero-based index of this entry within
            ``vpn.providers``.
        :param err_lines: Mutable list of error messages to append to on
            failure.
        :param resolver: A callable used to resolve ``credential_ref`` to
            a credential object (or ``None`` for unresolved).

        :returns: A ``VPNOverlayProfile`` on success, or ``None`` if the
            entry failed any validation step (in which case at least one
            line was appended to ``err_lines``).
    """
    if not isinstance(entry, dict):
        err_lines.append(f"vpn.providers[{idx}] must be a mapping.")
        rtnval = None
        return rtnval

    required = ("name", "provider", "network", "credential_ref")
    missing = [k for k in required if k not in entry]
    if len(missing) > 0:
        err_lines.append(
            f"vpn.providers[{idx}] missing required keys: {missing!r}."
        )
        rtnval = None
        return rtnval

    provider_value = entry["provider"]
    if provider_value not in SUPPORTED_VPN_PROVIDERS:
        err_lines.append(
            f"vpn.providers[{idx}].provider must be one of "
            f"{list(SUPPORTED_VPN_PROVIDERS)!r}; got {provider_value!r}."
        )
        rtnval = None
        return rtnval

    cred_ref = entry["credential_ref"]
    cred = _resolve_credential_ref(
        cred_ref=cred_ref,
        idx=idx,
        err_lines=err_lines,
        resolver=resolver,
    )
    if cred is None:
        rtnval = None
        return rtnval

    accepted = PROVIDER_CATEGORY_COMPATIBILITY[provider_value]
    cred_categories = list(getattr(cred, "categories", []))
    has_compatible = False
    for category in cred_categories:
        if category in accepted:
            has_compatible = True
            break

    if not has_compatible:
        err_lines.append(
            f"vpn.providers[{idx}].credential_ref={cred_ref!r} has categories "
            f"{cred_categories!r}; expected one of {sorted(accepted)!r} for "
            f"provider {provider_value!r}."
        )
        rtnval = None
        return rtnval

    profile_data = {
        "name": entry["name"],
        "provider": entry["provider"],
        "network": entry["network"],
        "tags": list(entry.get("tags", entry.get("default_tags", []))),
        "dns_suffix": entry.get("dns_suffix"),
        "magic_dns_enabled": bool(entry.get("magic_dns_enabled", False)),
        "acl_ref": entry.get("acl_ref"),
    }

    try:
        rtnval = VPNOverlayProfile.from_dict(data=profile_data)
    except ConfigurationError as ex:
        err_lines.append(f"vpn.providers[{idx}]: {ex}")
        rtnval = None

    return rtnval


def _resolve_credential_ref(*, cred_ref: Any, idx: int, err_lines: List[str],
                            resolver: CredentialLookup) -> Optional[Any]:
    """
        Resolves a ``credential_ref`` to a credential object using the
        supplied resolver, accumulating an error when unresolved.

        :param cred_ref: The raw ``credential_ref`` value (expected to be
            a non-empty string).
        :param idx: The zero-based index of this provider entry, used in
            the error message.
        :param err_lines: Mutable list of error messages to append to on
            failure.
        :param resolver: Callable that maps an identifier to a credential
            object or ``None``.

        :returns: The resolved credential object, or ``None`` when the
            reference is invalid or unresolved (in which case an error
            line is appended).
    """
    if not isinstance(cred_ref, str):
        err_lines.append(
            f"vpn.providers[{idx}].credential_ref must be a string."
        )
        rtnval = None
        return rtnval

    if len(cred_ref) == 0:
        err_lines.append(
            f"vpn.providers[{idx}].credential_ref must be a non-empty string."
        )
        rtnval = None
        return rtnval

    try:
        rtnval = resolver(cred_ref)
    except ConfigurationError:
        rtnval = None

    if rtnval is None:
        err_lines.append(
            f"vpn.providers[{idx}].credential_ref={cred_ref!r} did not resolve "
            "to any known credential identifier."
        )

    return rtnval


def _build_credential_resolver(*, injected: Optional[CredentialLookup]) -> CredentialLookup:
    """
        Builds the effective credential-lookup callable.

        When ``injected`` is supplied (typical for tests), it is returned
        unchanged. Otherwise this wraps the ``CredentialManagerSingleton``
        ``lookup_credential`` method and returns ``None`` when the manager
        has not yet been initialised (so the per-entry error message names
        the missing identifier rather than the operator being surprised
        by a ``SemanticError``).

        :param injected: Caller-supplied lookup callable, or ``None``.

        :returns: A callable matching the ``CredentialLookup`` signature.
    """
    if injected is not None:
        rtnval = injected
        return rtnval

    def _lookup(identifier: str) -> Optional[Any]:
        try:
            from ccai.credentials.wellknown import (  # type: ignore
                CREDENTIAL_MANAGER_SINGLETON,
            )
        except ImportError:
            CREDENTIAL_MANAGER_SINGLETON = None

        if CREDENTIAL_MANAGER_SINGLETON is None:
            rtnval = None
            return rtnval

        try:
            rtnval = CREDENTIAL_MANAGER_SINGLETON.lookup_credential(identifier)
        except ConfigurationError:
            rtnval = None

        return rtnval

    rtnval = _lookup
    return rtnval

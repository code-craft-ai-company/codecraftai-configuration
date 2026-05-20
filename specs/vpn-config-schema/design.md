# Design

## Overview

`vpn-config-schema` adds the `vpn:` top-level block schema to
`automojo-configuration`. It defines a single module —
`schemas/vpnconfigschema.py` — that contains a `VPNBlock` frozen
dataclass, a `load_vpn_block(data)` function that validates and
constructs the typed object from a parsed dict, and a
`dump_vpn_block(block)` function for the reverse direction.

The module reuses the existing typed classes:

- `VPNOverlayProfile` (from `automojo-networking`) — the shape of
  each `providers[*]` entry.
- `AddressPlane` (from `automojo-interfaces`) — the `default_plane`
  enum.
- The credential manager singleton (from `automojo-credentials`) —
  for `credential_ref` resolution and provider-compatibility check.

Per the §8 commitment "one spec, two read paths," `load_vpn_block`
is the one-way conversion from dict to typed object; every consumer
that needs the VPN configuration uses the typed object thereafter.

**See Also:** [vpn-overlay-profile](../../../automojo-networking/specs/vpn-overlay-profile/design.md),
[address-plane-types](../../../automojo-interfaces/specs/address-plane-types/design.md),
[tailscale-credentials](../../../automojo-credentials/specs/tailscale-credentials/design.md),
[twingate-credentials](../../../automojo-credentials/specs/twingate-credentials/design.md),
[well-known-vpn-and-venue-categories](../../../automojo-credentials/specs/well-known-vpn-and-venue-categories/design.md).

---

## Architecture

```
landscape.yaml / provisioning spec
        |
        | parsed YAML -> dict
        v
+----------------------------------------+
| load_vpn_block(data)                   |
|   - validate top-level shape           |
|   - resolve default_plane string ->    |
|       AddressPlane                     |
|   - for each provider entry:           |
|       resolve credential_ref via       |
|         CredentialManagerSingleton     |
|       validate provider/category       |
|         compatibility                  |
|       construct VPNOverlayProfile      |
|         via from_dict                  |
|   - accumulate all errors              |
|   - return VPNBlock                    |
+--------------------+-------------------+
                     |
                     v
+----------------------------------------+
| VPNBlock (frozen dataclass)            |
|   default_plane: AddressPlane          |
|   providers: List[VPNOverlayProfile]   |
+----------------------------------------+
        ^
        |
+----------------------------------------+
| dump_vpn_block(block) -> dict          |
| (credential refs not round-tripped)    |
+----------------------------------------+
```

---

## Data Model

```python
from dataclasses import dataclass, field
from typing import List
import os

from automojo.errors.exceptions import ConfigurationError
from automojo.interfaces.iaddressplane import AddressPlane
from automojo.networking.vpnoverlayprofile import (
    SUPPORTED_VPN_PROVIDERS,
    VPNOverlayProfile,
)
from automojo.credentials.wellknown import get_credentials_by_category


# Per-provider acceptable credential categories.
PROVIDER_CATEGORY_COMPATIBILITY = {
    "tailscale": {"tailscale-authkey", "tailscale-oauth"},
    "twingate":  {"twingate-service-account"},
}


@dataclass(frozen=True)
class VPNBlock:
    """
        Typed representation of the `vpn:` top-level block.

        :param default_plane: Default address plane used by callers that do
            not specify one. Defaults to PUBLIC per §5 design decision.
        :param providers: List of overlay profiles configured for this
            landscape / spec.
    """
    default_plane: AddressPlane = AddressPlane.PUBLIC
    providers: List[VPNOverlayProfile] = field(default_factory=list)


def load_vpn_block(*, data: dict) -> VPNBlock:
    """
        Parses and validates the `vpn:` block of a parsed config dict.

        :param data: The dict value of the `vpn:` key, or {} when absent.

        :returns: A typed VPNBlock.
        :raises: ConfigurationError accumulating every validation failure.
    """
    err_lines: List[str] = []

    default_plane = _parse_default_plane(
        raw=data.get("default_plane", "PUBLIC"),
        err_lines=err_lines,
    )

    providers_raw = data.get("providers", [])
    providers: List[VPNOverlayProfile] = []
    if not isinstance(providers_raw, list):
        err_lines.append("vpn.providers must be a list.")
    else:
        for idx, entry in enumerate(providers_raw):
            profile = _parse_provider_entry(
                entry=entry,
                idx=idx,
                err_lines=err_lines,
            )
            if profile is not None:
                providers.append(profile)

    if default_plane == AddressPlane.OVERLAY and len(providers) == 0:
        err_lines.append(
            "vpn.default_plane=OVERLAY requires at least one entry in vpn.providers."
        )

    if len(err_lines) > 0:
        msg_lines = ["vpn-config-schema validation failed:"]
        msg_lines.extend("  - " + line for line in err_lines)
        err_msg = os.linesep.join(msg_lines)
        raise ConfigurationError(err_msg)

    rtnval = VPNBlock(default_plane=default_plane, providers=providers)
    return rtnval


def _parse_default_plane(*, raw, err_lines: List[str]) -> AddressPlane:
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


def _parse_provider_entry(*, entry, idx: int, err_lines: List[str]):
    if not isinstance(entry, dict):
        err_lines.append(f"vpn.providers[{idx}] must be a mapping.")
        return None
    required = ("name", "provider", "network", "credential_ref")
    missing = [k for k in required if k not in entry]
    if len(missing) > 0:
        err_lines.append(
            f"vpn.providers[{idx}] missing required keys: {missing!r}."
        )
        return None
    provider = entry["provider"]
    if provider not in SUPPORTED_VPN_PROVIDERS:
        err_lines.append(
            f"vpn.providers[{idx}].provider must be one of "
            f"{SUPPORTED_VPN_PROVIDERS}; got {provider!r}."
        )
        return None
    cred_ref = entry["credential_ref"]
    cred = _resolve_credential_ref(cred_ref=cred_ref, err_lines=err_lines, idx=idx)
    if cred is not None:
        accepted = PROVIDER_CATEGORY_COMPATIBILITY[provider]
        if not any(c in accepted for c in cred.categories):
            err_lines.append(
                f"vpn.providers[{idx}].credential_ref={cred_ref!r} has categories "
                f"{cred.categories!r}; expected one of {sorted(accepted)!r} for "
                f"provider {provider!r}."
            )
            return None
    try:
        rtnval = VPNOverlayProfile.from_dict(data=entry)
    except ConfigurationError as ex:
        err_lines.append(f"vpn.providers[{idx}]: {ex}")
        rtnval = None
    return rtnval


def _resolve_credential_ref(*, cred_ref: str, err_lines: List[str], idx: int):
    # Pseudocode — concrete lookup uses get_credential_by_identifier
    # on the singleton. Returns None on miss.
    ...


def dump_vpn_block(*, block: VPNBlock) -> dict:
    rtnval = {
        "default_plane": block.default_plane.name,
        "providers": [
            {
                "name": p.name,
                "provider": p.provider,
                "network": p.network,
                "tags": list(p.tags),
                "dns_suffix": p.dns_suffix,
                "magic_dns_enabled": p.magic_dns_enabled,
                "acl_ref": p.acl_ref,
                # credential_ref intentionally omitted on dump
            }
            for p in block.providers
        ],
    }
    return rtnval
```

---

## Module Layout

```
automojo-configuration/source/packages/automojo/configuration/
  schemas/
    __init__.py
    vpnconfigschema.py   <-- VPNBlock, load_vpn_block, dump_vpn_block,
                              PROVIDER_CATEGORY_COMPATIBILITY
  configurationloader.py (existing — register the new schema here)
```

---

## See Also

- [vpn-overlay-profile](../../../automojo-networking/specs/vpn-overlay-profile/design.md)
  — the typed object each `providers[*]` entry becomes.
- [address-plane-types](../../../automojo-interfaces/specs/address-plane-types/design.md)
  — supplies `AddressPlane`.
- [tailscale-credentials](../../../automojo-credentials/specs/tailscale-credentials/design.md),
  [twingate-credentials](../../../automojo-credentials/specs/twingate-credentials/design.md)
  — supply the credential categories validated by
  `PROVIDER_CATEGORY_COMPATIBILITY`.
- [well-known-vpn-and-venue-categories](../../../automojo-credentials/specs/well-known-vpn-and-venue-categories/design.md)
  — supplies the credential lookup surface.

---

## Testing Strategy

- **No-block backward compat.** Loading a config with no `vpn:` key
  yields `VPNBlock(default_plane=PUBLIC, providers=[])`.
- **Defaults.** `vpn: {}` yields the same default block.
- **Happy path.** A complete `vpn:` block parses into a `VPNBlock`
  with the expected `default_plane` and `providers` list.
- **Missing-keys error.** Provider entry missing `network` raises
  `ConfigurationError` with the missing key listed.
- **Unknown provider.** `provider: meraki` raises with the
  supported-providers list in the message.
- **Bad default_plane.** `default_plane: WAN` raises with the
  accepted values listed.
- **OVERLAY default with no providers.** Raises the dedicated
  message.
- **Credential ref unresolved.** Raises with the missing identifier
  named.
- **Credential category mismatch.** Tailscale provider referencing
  a Twingate credential raises with both the offending categories
  and the accepted set named.
- **Multi-error accumulation.** Two simultaneous failures both
  appear in the raised message, each on its own line.
- **dump round-trip.** `dump_vpn_block(load_vpn_block(data))` is
  equal to `data` when `data` does not contain `credential_ref`
  (i.e. credential refs are intentionally not round-tripped).
- **No property tests required** — the schema is a small fixed
  shape with explicit validation rules. Property tests for the
  algebraic invariants of `VPNOverlayProfile` and `AddressPlane`
  live in their own specs.

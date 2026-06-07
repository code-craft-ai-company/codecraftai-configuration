# Requirements

## Introduction

The `vpn-config-schema` feature adds a schema fragment for the new
top-level `vpn:` block in `landscape.yaml` (and any other ccai
config document that consumes the same shape) to
`codecraftai-configuration`. The schema captures:

- a list of VPN providers under a landscape / spec
- per-provider credential reference (looked up by category in
  `codecraftai-credentials`)
- per-provider default tags
- the landscape-wide default `address_plane` (`PUBLIC` / `PRIVATE` /
  `OVERLAY`)

This single source of truth means landscape loaders, provisioning
loaders, and `arcli` all parse and validate the same shape — the
§8 commitment "one spec, two read paths: typed object + dict" applies
here as well.

This spec does *not* define the runtime classes (those live in
`vpn-overlay-profile`, `tailscale-credentials`,
`twingate-credentials`, `address-plane-types`). It defines the
*schema* that converts a YAML/dict blob into those typed objects with
validation.

**See Also:** [vpn-overlay-profile](../../../codecraftai-networking/specs/vpn-overlay-profile/design.md),
[tailscale-credentials](../../../codecraftai-credentials/specs/tailscale-credentials/design.md),
[twingate-credentials](../../../codecraftai-credentials/specs/twingate-credentials/design.md),
[address-plane-types](../../../codecraftai-interfaces/specs/address-plane-types/design.md),
[well-known-vpn-and-venue-categories](../../../codecraftai-credentials/specs/well-known-vpn-and-venue-categories/design.md).

---

## Requirements

### Requirement 1: Schema Module Location

**User Story:** As a config-loader implementer, I want all
VPN-related schema in one module so I do not chase fragments.

#### Acceptance Criteria

1. THE SYSTEM SHALL place the schema under
   `codecraftai-configuration/source/packages/ccai/configuration/schemas/vpnconfigschema.py`.
2. THE SYSTEM SHALL register the schema with the existing
   configuration loader so the `vpn:` top-level key is recognised
   and validated automatically.

---

### Requirement 2: Top-Level `vpn:` Block Shape

**User Story:** As a landscape author, I want a single declarative
block to describe the overlay providers available in a landscape.

#### Acceptance Criteria

1. THE SYSTEM SHALL accept a top-level `vpn:` block matching the
   shape:
   ```yaml
   vpn:
     default_plane: PUBLIC          # PUBLIC | PRIVATE | OVERLAY
     providers:
       - name: lab-tailnet           # VPNOverlayProfile.name
         provider: tailscale         # tailscale | twingate
         network: acme.ts.net
         credential_ref: ts-prov-oauth
         default_tags: [tag:lab]
         dns_suffix: null
         magic_dns_enabled: true
         acl_ref: null
   ```
2. THE SYSTEM SHALL require `providers` to be a list of zero or
   more entries.
3. THE SYSTEM SHALL default `default_plane` to `"PUBLIC"` when
   absent (matching §5 of the design plan).

---

### Requirement 3: Per-Provider Entry Validation

**User Story:** As a config-loader, I want each provider entry
validated against the same rules `VPNOverlayProfile` enforces, so
errors surface at load time, not at first use.

#### Acceptance Criteria

1. THE SYSTEM SHALL require `name`, `provider`, `network`, and
   `credential_ref` on every provider entry; raise
   `ConfigurationError` with the missing-key list otherwise.
2. THE SYSTEM SHALL validate `provider in SUPPORTED_VPN_PROVIDERS`
   (from `vpnoverlayprofile.py`).
3. THE SYSTEM SHALL validate that `credential_ref` resolves to an
   existing credential identifier in the credential manager; raise
   `ConfigurationError` listing the unresolved reference otherwise.
4. THE SYSTEM SHALL validate that the referenced credential has a
   provider-compatible category
   (`tailscale-authkey` or `tailscale-oauth` for
   `provider=tailscale`; `twingate-service-account` for
   `provider=twingate`).

---

### Requirement 4: Default Plane Validation

**User Story:** As a config-loader, I want `default_plane` to map
cleanly to `AddressPlane`.

#### Acceptance Criteria

1. THE SYSTEM SHALL accept the string values `"PUBLIC"`,
   `"PRIVATE"`, `"OVERLAY"` (case-insensitive) and map them to the
   corresponding `AddressPlane` member.
2. WHEN `default_plane` is `"OVERLAY"` and the `providers` list is
   empty THE SYSTEM SHALL raise `ConfigurationError` (no overlay
   provider configured to support the default).
3. WHEN `default_plane` is not a recognised value THE SYSTEM SHALL
   raise `ConfigurationError`.

---

### Requirement 5: Typed Output

**User Story:** As a downstream consumer, I want the schema's
`load(...)` function to return typed objects, not a raw dict.

#### Acceptance Criteria

1. THE SYSTEM SHALL provide
   `load_vpn_block(*, data: dict) -> VPNBlock` where `VPNBlock`
   is a frozen dataclass with fields
   `default_plane: AddressPlane`, `providers: List[VPNOverlayProfile]`.
2. THE SYSTEM SHALL also expose
   `dump_vpn_block(*, block: VPNBlock) -> dict` for the reverse
   direction so configs can be regenerated.
3. THE SYSTEM SHALL document that `dump_vpn_block` does *not*
   round-trip the `credential_ref` field of any provider —
   credentials are stored by identifier and looked up at load time,
   not embedded.

---

### Requirement 6: Multiple Error Accumulation

**User Story:** As an operator, I want every error in my config
reported in one pass.

#### Acceptance Criteria

1. WHEN multiple validation failures are present THE SYSTEM SHALL
   accumulate them into a single `ConfigurationError` whose message
   lists each failure on its own line.
2. THE SYSTEM SHALL build the multi-line message using the standard
   `os.linesep.join(lines)` pattern from the project coding
   standards.

---

### Requirement 7: No Behaviour-Change for Existing Configs

**User Story:** As an existing landscape author with no `vpn:`
block, I want my config to keep loading unchanged.

#### Acceptance Criteria

1. WHEN no `vpn:` block is present THE SYSTEM SHALL produce a
   `VPNBlock` with `default_plane=AddressPlane.PUBLIC` and an
   empty `providers` list, and no warning.
2. THE SYSTEM SHALL NOT alter any other configuration schema.

# Requirements

## Introduction

This spec defines the YAML configuration schema fragments that `automojo-configuration`
exposes for cloud provisioning specs.  It covers the top-level keys
`networks`, `subnets`, `security_groups`, `keypairs`, `accelerators`,
`shared_filesystems`, `devices[*].vpn_join`, and per-venue override blocks consumed
by `automojo-provisioning`.

The schema fragments live in `automojo-configuration` (not in
`automojo-provisioning`) so every consumer that loads provisioning YAML — engine,
CLI, tests, downstream users — shares one parser and one validator.  The fragments
defer to the model classes in `automojo-provisioning` for shape validation via
`SchemaObject.from_dict`; this spec owns only the schema **fragment definitions**, the
**file format**, and the **registration with the config loader**.

---

## Requirements

### Requirement 1: Top-Level Schema Block Registration

**User Story:** As a config consumer, I want to load a provisioning YAML and have
every block parsed into typed objects in one call.

#### Acceptance Criteria

1. THE SYSTEM SHALL register schema fragments for these top-level keys:
   `networks`, `subnets`, `security_groups`, `keypairs`, `accelerators`,
   `shared_filesystems`, `venues`, `devices`.
2. WHEN a key is absent THE SYSTEM SHALL default to an empty list (no error).
3. WHEN a key is present and its content fails schema validation THE SYSTEM SHALL
   raise `ConfigurationError` identifying the offending entry by line.

---

### Requirement 2: networks Block

**User Story:** As a provisioning author, I want to list the VPCs I need.

#### Acceptance Criteria

1. THE SYSTEM SHALL accept entries with required fields: `name`, `cidr`, `region`.
2. THE SYSTEM SHALL accept optional `tags` as a list of single-key dicts.
3. WHEN any required field is missing THE SYSTEM SHALL raise
   `ConfigurationError`.

---

### Requirement 3: subnets, security_groups, keypairs Blocks

**User Story:** As a provisioning author, I want subnet, SG, and keypair lists
defined alongside networks.

#### Acceptance Criteria

1. THE SYSTEM SHALL parse `subnets` entries into `CloudSubnet`.
2. THE SYSTEM SHALL parse `security_groups` entries into `CloudSecurityGroup` with
   nested `ingress_rules` and `egress_rules`.
3. THE SYSTEM SHALL parse `keypairs` entries into `CloudKeyPair`.
4. WHEN any nested object fails its schema THE SYSTEM SHALL surface the original
   error with the YAML path.

---

### Requirement 4: accelerators Block

**User Story:** As an AI-workload author, I want an accelerator section that maps to
the catalog.

#### Acceptance Criteria

1. THE SYSTEM SHALL accept entries with `name` (instance reference) and
   `accelerators: List[CloudAcceleratorSpec]` fields.
2. WHEN a referenced neutral name is not present in the
   [accelerator-catalog](../../../automojo-provisioning/specs/accelerator-catalog/design.md)
   THE SYSTEM SHALL raise `ConfigurationError`.

---

### Requirement 5: shared_filesystems Block

**User Story:** As an AI-workload author, I want shared FS declarations parsed
alongside compute.

#### Acceptance Criteria

1. THE SYSTEM SHALL parse entries into `CloudSharedFilesystem`.
2. WHEN both `existing_id` and `size_tb` are absent THE SYSTEM SHALL raise
   `ConfigurationError` (attach-or-provision discriminator).

---

### Requirement 6: devices[*].vpn_join Sub-Block

**User Story:** As a provisioning author, I want each device to optionally declare
how it joins the mesh.

#### Acceptance Criteria

1. THE SYSTEM SHALL parse the `vpn_join` sub-block into `VPNJoinSpec`.
2. WHEN `vpn_join.control_plane_credential` does not resolve to a registered
   credential THE SYSTEM SHALL raise `ConfigurationError`.
3. WHEN `vpn_join` is absent THE SYSTEM SHALL leave the field as `None`.

---

### Requirement 7: Per-Venue Override Blocks

**User Story:** As a provisioning author, I want to attach venue-specific overrides
without leaking them into the neutral model.

#### Acceptance Criteria

1. THE SYSTEM SHALL accept a per-venue override map under
   `venues[*].overrides: Dict[str, Any]` and forward it to the venue plugin as-is.
2. THE SYSTEM SHALL NOT validate the override contents; the venue plugin owns its
   own override schema.
3. WHEN a venue plugin reports an unknown override key THE SYSTEM SHALL log a
   warning (not an error) — overrides are forward-compatible.

---

### Requirement 8: Loader API

**User Story:** As a downstream consumer, I want one function to load a complete
provisioning config.

#### Acceptance Criteria

1. THE SYSTEM SHALL expose
   `load_cloud_provisioning_config(*, path: str) -> CloudProvisioningConfig`
   returning a typed object containing every parsed list.
2. THE SYSTEM SHALL expose `validate_cloud_provisioning_config(*, payload: dict)
   -> None` that callers use without loading from disk.

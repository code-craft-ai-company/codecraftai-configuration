# Requirements

## Introduction

This spec defines the YAML schema fragments for workload-shaped venues
(`WorkloadVenue`, `WorkloadCluster`, `WorkloadJob`, `WorkloadService`).  Like its
cloud-side sibling, the fragments live in `automojo-configuration` so every consumer
(engine, CLI, tests, downstream users) shares one parser and one validator.

Workload specs are usually authored in the *same* YAML file as cloud specs (the engine
drives a mixed list of `CloudVenue` and `WorkloadVenue` entries).  This spec defines
fragments that compose cleanly with `cloud-provisioning-config-schema` — together
they describe a complete provisioning input.

Only `KUBERNETES` is implemented in v1.  Schema fragments for `SLURM`, `RAY`, `NOMAD`
are present but the engine's apply path raises `NotImplementedError` for those kinds
(per §7.6 plan decision).

---

## Requirements

### Requirement 1: Top-Level Block Registration

**User Story:** As a config consumer, I want workload blocks parsed alongside cloud
blocks in one load.

#### Acceptance Criteria

1. THE SYSTEM SHALL register schema fragments for:
   `workload_venues`, `workload_clusters`, `workload_jobs`, `workload_services`.
2. WHEN any of these keys is absent THE SYSTEM SHALL default to an empty list.
3. WHEN any entry fails its model `from_dict` THE SYSTEM SHALL raise
   `ConfigurationError` identifying the offending entry by line.

---

### Requirement 2: workload_venues Block

**User Story:** As a workload-spec author, I want to declare K8s / Slurm / Ray /
Nomad venues.

#### Acceptance Criteria

1. THE SYSTEM SHALL parse entries into `WorkloadVenue`.
2. WHEN `kind` is not a `WorkloadVenueKind` value THE SYSTEM SHALL raise
   `ConfigurationError`.
3. WHEN `credential_ref` does not resolve to a known credential THE SYSTEM SHALL
   raise `ConfigurationError`.
4. WHERE the credential type is incompatible with the declared `kind` (e.g. a
   `KubeconfigCredential` paired with `kind: slurm`) THE SYSTEM SHALL raise
   `ConfigurationError`.

---

### Requirement 3: workload_clusters Block

**User Story:** As a workload author, I want to declare long-lived clusters with
node pools.

#### Acceptance Criteria

1. THE SYSTEM SHALL parse entries into `WorkloadCluster`.
2. THE SYSTEM SHALL parse nested `node_pools` and `accelerator_pools` into
   `NodePoolSpec` lists.
3. WHEN any node pool's `accelerators[*].model` is not in the accelerator catalog
   THE SYSTEM SHALL raise `ConfigurationError`.

---

### Requirement 4: workload_jobs Block

**User Story:** As a workload author, I want to declare batch jobs.

#### Acceptance Criteria

1. THE SYSTEM SHALL parse entries into `WorkloadJob`.
2. WHEN `replicas <= 0` or `restart_policy` is not in
   `{"Never", "OnFailure"}` THE SYSTEM SHALL raise `ConfigurationError`.
3. WHEN nested `shared_fs_mounts` references a `filesystem_name` not declared in
   the spec THE SYSTEM SHALL raise `ConfigurationError`.

---

### Requirement 5: workload_services Block

**User Story:** As a workload author, I want to declare long-running services
(inference endpoints, JupyterHub).

#### Acceptance Criteria

1. THE SYSTEM SHALL parse entries into `WorkloadService`.
2. WHEN `exposure` is not in `{"ClusterIP", "LoadBalancer", "NodePort"}` THE SYSTEM
   SHALL raise `ConfigurationError`.
3. WHERE `exposure == "LoadBalancer"` and the referenced venue's capability matrix
   says no LB support THE SYSTEM SHALL raise `ConfigurationError`.

---

### Requirement 6: Composition with Cloud Spec

**User Story:** As a workload author, I want a single YAML to declare both
self-hosted cloud infrastructure AND the workload running on it.

#### Acceptance Criteria

1. THE SYSTEM SHALL allow `workload_venues[*].cloud_provisioner_ref` to name a
   `CloudVenue` from the same spec.
2. WHEN the named reference does not exist THE SYSTEM SHALL raise
   `ConfigurationError`.
3. WHEN composition is declared THE SYSTEM SHALL signal the engine to apply the
   referenced cloud venue before the workload venue (and reverse on destroy).

---

### Requirement 7: Loader API

**User Story:** As a downstream consumer, I want one function to load a workload
config.

#### Acceptance Criteria

1. THE SYSTEM SHALL expose
   `load_workload_provisioning_config(*, path: str) -> WorkloadProvisioningConfig`.
2. THE SYSTEM SHALL expose `validate_workload_provisioning_config(*, payload: dict)
   -> None`.
3. WHEN the same path is loaded with `load_cloud_provisioning_config` and
   `load_workload_provisioning_config` THE SYSTEM SHALL accept the combined view as
   a single coherent spec.

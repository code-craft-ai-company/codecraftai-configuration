# Implementation Plan — Workload Provisioning Config Schema

## Fragment Definitions

- [x] 1. Create `workloadprovisioningfragment.py`
- [x] 2. Register `workload_venues` fragment → `WorkloadVenue`
- [x] 3. Register `workload_clusters` fragment → `WorkloadCluster`
- [x] 4. Register `workload_jobs` fragment → `WorkloadJob`
- [x] 5. Register `workload_services` fragment → `WorkloadService`

## Aggregate

- [x] 6. Create `workloadprovisioningconfig.py` — `WorkloadProvisioningConfig(SchemaObject)`

## Loader / Validator

- [x] 7. Create `workloadprovisioningloader.py`
- [x] 8. Implement `load_workload_provisioning_config(path)`
- [x] 9. Implement `validate_workload_provisioning_config(payload)`
- [x] 10. Raise `ConfigurationError` with YAML path on failure
- [x] 11. Validate `kind`, `exposure`, `restart_policy` literal membership
- [x] 12. Cross-reference `shared_fs_mounts.filesystem_name` to declared shared FS
- [x] 13. Cross-reference node-pool accelerators to catalog
- [x] 14. Validate `workload_venues[*].cloud_provisioner_ref` against cloud venues
- [x] 15. Resolve `credential_ref` against credential vault per `kind`

## Tests

- [x] 16. `test_load_minimal_workload_config`
- [x] 17. `test_load_full_workload_config_with_every_block`
- [x] 18. `test_missing_top_level_key_defaults_to_empty_list`
- [x] 19. `test_unknown_workload_kind_fails`
- [x] 20. `test_unknown_exposure_fails`
- [x] 21. `test_node_pool_accelerator_unknown_model_fails`
- [x] 22. `test_cloud_provisioner_ref_unknown_fails`
- [x] 23. `test_credential_type_mismatch_fails`
- [x] 24. `test_coexistence_with_cloud_config_in_one_file`
- [x] 25. `test_loadbalancer_exposure_rejected_when_venue_unsupported`

## Documentation

- [x] 26. Document fragment registration in module docstring
- [x] 27. Cross-link `workload-venue-model` and `cloud-provisioning-config-schema`
- [x] 28. Document §7.6 K8s-only v1 with SLURM/RAY/NOMAD NIE

## Notes

Items 13, 21, 23, 25 are intentionally deferred. They depend on:

- Accelerator-catalog upstream type (`accelerator-catalog` spec in
  `automojo-provisioning`, Phase 1a) for model-name validation.
- The `CoreweaveApiCredential` / typed credential class hierarchy for
  kind-vs-credential cross checks (Phase 1a / 1b).
- The venue capability-matrix module for LB-support validation (Phase 2).

These items will be picked up in the follow-on pass once the upstream types
land.

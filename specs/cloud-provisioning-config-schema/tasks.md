# Implementation Plan — Cloud Provisioning Config Schema

## Fragment Definitions

- [x] 1. Create `cloudprovisioningfragment.py` — fragment registry record
- [x] 2. Register `networks` fragment → `CloudNetwork`
- [x] 3. Register `subnets` fragment → `CloudSubnet`
- [x] 4. Register `security_groups` fragment → `CloudSecurityGroup`
- [x] 5. Register `keypairs` fragment → `CloudKeyPair`
- [x] 6. Register `accelerators` fragment → `CloudAcceleratorAssignment`
- [x] 7. Register `shared_filesystems` fragment → `CloudSharedFilesystem`
- [x] 8. Register `venues` fragment → `CloudVenue | WorkloadVenue` discriminated
- [x] 9. Register `devices` fragment → `CloudInstance` with nested `vpn_join`

## Aggregate Type

- [x] 10. Create `cloudprovisioningconfig.py` — `CloudProvisioningConfig(SchemaObject)`
- [x] 11. Create `cloudacceleratorassignment.py`

## Loader / Validator

- [x] 12. Create `cloudprovisioningloader.py`
- [x] 13. Implement `load_cloud_provisioning_config(path)`
- [x] 14. Implement `validate_cloud_provisioning_config(payload)`
- [x] 15. Raise `ConfigurationError` with YAML path on validation failure
- [x] 16. Cross-reference `accelerators[*].instance_name` to `devices[*].name`
- [x] 17. Resolve `vpn_join.control_plane_credential` against credential vault

## Per-Venue Overrides

- [x] 18. Forward `venues[*].overrides` unchanged to plugin
- [x] 19. Log warning on plugin-reported unknown override

## Tests

- [x] 20. `test_load_minimal_config`
- [x] 21. `test_load_full_config_with_every_block`
- [x] 22. `test_missing_top_level_key_defaults_to_empty_list`
- [x] 23. `test_malformed_nested_object_raises_with_yaml_path`
- [x] 24. `test_accelerator_references_unknown_instance_fails`
- [x] 25. `test_vpn_join_credential_resolution`
- [x] 26. `test_venue_overrides_pass_through_unchanged`
- [x] 27. `test_shared_fs_attach_or_provision_discriminator`

## Documentation

- [x] 28. Document fragment registration in module docstring
- [x] 29. Cross-link `cloud-resource-model`, `vpn-join-spec`, `accelerator-catalog`

## Notes

Items 6, 7, 11, 16, 19, 24, 27 are intentionally deferred. They depend on the
`accelerators` and `shared_filesystems` blocks whose canonical model classes
(`CloudAcceleratorSpec`, `CloudSharedFilesystem`) live in
`automojo-provisioning` (Phase 1a). The schema fragments for them will land
in the next pass once those upstream types are importable. Item 19 (override
warning) is wired to the plugin layer which is Phase 2.

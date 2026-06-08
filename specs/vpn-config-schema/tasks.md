# Implementation Plan — VPN Config Schema

## Module and Models

- [x] 1. Create `codecraftai-configuration/source/packages/ccai/configuration/schemas/__init__.py`
  if not already present.
- [x] 2. Create `codecraftai-configuration/source/packages/ccai/configuration/schemas/vpnconfigschema.py`.
- [x] 3. Define `PROVIDER_CATEGORY_COMPATIBILITY` mapping
  (`tailscale -> {tailscale-authkey, tailscale-oauth}`,
  `twingate -> {twingate-service-account}`).
- [x] 4. Define `VPNBlock(frozen=True)` dataclass with
  `default_plane: AddressPlane = PUBLIC` and
  `providers: List[VPNOverlayProfile]`.

## load_vpn_block — To Implement

- [x] 5. Implement `load_vpn_block(*, data)` with multi-error
  accumulation into `err_lines` (per project standards using
  `os.linesep.join`).
- [x] 6. Implement `_parse_default_plane(*, raw, err_lines)` handling
  case-insensitive PUBLIC / PRIVATE / OVERLAY.
- [x] 7. Implement `_parse_provider_entry(*, entry, idx, err_lines)`
  validating required keys, `provider` membership in
  `SUPPORTED_VPN_PROVIDERS`, credential resolution, and provider /
  category compatibility.
- [x] 8. Implement `_resolve_credential_ref(*, cred_ref, err_lines,
  idx)` calling into the credential manager singleton.
- [x] 9. Enforce: `default_plane == OVERLAY` AND empty providers list
  is a `ConfigurationError`.
- [x] 10. Construct `VPNOverlayProfile` from each valid entry via
  `from_dict`; catch and re-record `ConfigurationError` from
  per-profile validation.

## dump_vpn_block — To Implement

- [x] 11. Implement `dump_vpn_block(*, block) -> dict`. Do NOT emit
  `credential_ref` on dump (documented one-way field).

## Loader Registration

- [x] 12. Register the schema with the existing configuration loader
  so a top-level `vpn:` key is parsed automatically.

## Testing

- [x] 13. `test_no_block_yields_default_vpnblock`.
- [x] 14. `test_empty_block_yields_default_vpnblock`.
- [x] 15. `test_happy_path_parses_into_typed_block`.
- [x] 16. `test_missing_provider_key_raises_with_key_list`.
- [x] 17. `test_unknown_provider_raises_with_supported_list`.
- [x] 18. `test_bad_default_plane_raises_with_accepted_list`.
- [x] 19. `test_overlay_default_with_no_providers_raises`.
- [x] 20. `test_unresolved_credential_ref_raises_with_identifier`.
- [x] 21. `test_credential_category_mismatch_raises`.
- [x] 22. `test_multi_error_accumulation_lists_each_failure`.
- [x] 23. `test_dump_round_trip_excludes_credential_ref`.
- [x] 24. `test_loader_registers_top_level_vpn_key`.

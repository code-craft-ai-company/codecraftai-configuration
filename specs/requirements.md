# AutoMojo Configuration Package Requirements

## Introduction

The AutoMojo Configuration package provides a multi-source, multi-format configuration loading system with encryption support, environment variable management, configuration map merging, and bidirectional synchronization to remote stores. It supports five configuration categories (credentials, landscapes, topologies, runtimes, data profiles) loaded from directory, HTTP, CouchDB, and MongoDB sources. This document provides implementation-level detail sufficient for porting the functionality to another language.

## Source Module Map

| Source Module | Purpose |
|---|---|
| `configurationformat.py` | `ConfigurationFormat` enum (JSON, YAML) |
| `configurationloader.py` | `ConfigurationLoader` — multi-source config loading with encryption |
| `configurationmaps.py` | Per-type config resolution functions, `CONFIGURATION_MAPS` singleton |
| `configurationsettings.py` | `ConfigurationDefaults`, `establish_configuration_settings()` |
| `configurationvariables.py` | `ConfigVariablesDesc`, `ConfigVariables`, `resolve_configuration_variables()` |
| `cryptography.py` | Fernet encryption/decryption, key generation from keyphrase |
| `defaultvalues.py` | `DefaultValues.NotSet` sentinel |
| `normalize.py` | Input normalization helpers (name lists, path lists, source lists) |
| `optionoverrides.py` | `ConfigOptionOverrides` — per-type override static methods |
| `sources/configurationsourcebase.py` | `ConfigurationSourceBase` abstract base |
| `sources/directorysource.py` | `DirectorySource` — filesystem config loading |
| `sources/httpsource.py` | `HttpSource` — HTTP/HTTPS config loading |
| `sources/couchdbsource.py` | `CouchDBSource` — CouchDB config loading |
| `sources/mongodbsource.py` | `MongoDBSource` — MongoDB config loading |
| `synchronization/configsynchronizerbase.py` | `ConfigSynchronizerBase` abstract base |
| `synchronization/directoryconfigsynchronizer.py` | Directory-based sync |
| `synchronization/couchdbconfigsynchronizer.py` | CouchDB-based sync |
| `synchronization/mongodbconfigsynchronizer.py` | MongoDB-based sync |
| `synchronization/githubconfigsynchronizer.py` | GitHub repository sync |

---

## Requirements

### Requirement 1: Configuration Format Enumeration

**User Story:** As a framework developer, I want a typed enumeration of supported configuration formats, so that format handling is consistent.

#### Acceptance Criteria

1. THE `ConfigurationFormat` enum SHALL define two values: `JSON = "json"` and `YAML = "yaml"`.
2. THE enum SHALL be a string enum for serialization compatibility.
3. THE enum SHALL be used throughout the system to identify configuration file formats.

---

### Requirement 2: Configuration Loader

**User Story:** As a developer, I want to load configurations from multiple sources by name or file path, with automatic encryption handling, so that configurations are resolved from the first available source.

#### Acceptance Criteria

1. THE `ConfigurationLoader` SHALL accept a list of source URI strings, optional credentials mapping (`dict[string, (string, string)]` — host to user/password), and optional `verify_certificate` flag (default: `true`).
2. WHEN initialized, THE loader SHALL parse each URI and create the appropriate source instance:
   - URIs starting with `couchdb://` → `CouchDBSource`
   - URIs starting with `mongodb://` → `MongoDBSource`
   - URIs starting with `http://` or `https://` → `HttpSource`
   - All other URIs → `DirectorySource`
3. IF a source URI fails to parse, THE loader SHALL raise a `ConfigurationError` with the URI in the message.
4. WHEN `load_configuration_by_name(config_name, key?, keyphrase?)` is called, THE loader SHALL iterate through sources calling `try_load_configuration(config_name, credentials)` on each, returning the first non-None result as `(config_uri, config_data)`.
5. IF no source returns a configuration, THE loader SHALL raise a `ConfigurationError` listing all checked source URIs.
6. WHEN `load_configuration_from_file(config_file, key?, keyphrase?)` is called, THE loader SHALL load directly from the file path, detecting format by extension (`.yaml`/`.yml` → YAML, `.json` → JSON).
7. IF an unsupported file extension is encountered, THE loader SHALL raise a `ConfigurationError`.
8. IF both `key` and `keyphrase` are provided, THE loader SHALL raise a `SemanticError` — only one is allowed.
9. WHEN the loaded configuration contains an `"encrypted_content"` key, THE loader SHALL decrypt it using the provided key (or key derived from keyphrase), parse the decrypted content according to the `"format"` field, and return the decrypted data.
10. IF encrypted content is found but no key or keyphrase is provided, THE loader SHALL raise a `ConfigurationError`.

---

### Requirement 3: Configuration Source Base

**User Story:** As a framework developer, I want an abstract base for configuration sources, so that new source types can be added.

#### Acceptance Criteria

1. THE `ConfigurationSourceBase` SHALL define a `scheme` class attribute identifying the URI scheme.
2. THE base SHALL store the source `uri` and expose it as a property.
3. THE base SHALL define an abstract `parse(uri) -> Option[ConfigurationSourceBase]` class method.
4. THE base SHALL define an abstract `try_load_configuration(config_name, credentials?) -> (ConfigurationFormat?, dict?)` method returning `(format, data)` on success or `(None, None)` on not-found.

---

### Requirement 4: Directory Source

**User Story:** As a developer, I want to load configurations from local filesystem directories, so that configurations can be stored as files.

#### Acceptance Criteria

1. THE `DirectorySource` SHALL have scheme `"dir"` and parse URIs matching `dir://(?P<directory>.+)`.
2. IF the URI does not match the `dir://` pattern, THE source SHALL treat the entire URI as a directory path.
3. THE directory path SHALL be expanded using environment variable and home directory expansion.
4. WHEN `try_load_configuration` is called, THE source SHALL search for `{config_name}.yaml`, `{config_name}.yml`, `{config_name}.json` in the directory (in that order), returning the first found.
5. IF the file is empty, THE source SHALL return an empty dictionary (not None).

---

### Requirement 5: HTTP Source

**User Story:** As a developer, I want to load configurations from HTTP/HTTPS endpoints, so that configurations can be served remotely.

#### Acceptance Criteria

1. THE `HttpSource` SHALL support both `http://` and `https://` schemes.
2. WHEN `try_load_configuration` is called, THE source SHALL try GET requests for `{base_url}/{config_name}.yaml`, `.yml`, `.json` (in that order), returning the first successful response (HTTP 200).
3. THE source SHALL parse the response content according to the detected format.

---

### Requirement 6: CouchDB Source

**User Story:** As a developer, I want to load configurations from CouchDB databases, so that configurations can be stored in a document database.

#### Acceptance Criteria

1. THE `CouchDBSource` SHALL parse URIs matching the `couchdb://` scheme.
2. THE source SHALL connect to the CouchDB instance and look up the configuration document by name.
3. IF the `couchdb` library is not installed, THE source SHALL raise an `ImportError` with a clear message.

---

### Requirement 7: MongoDB Source

**User Story:** As a developer, I want to load configurations from MongoDB databases, so that configurations can be stored in a document database.

#### Acceptance Criteria

1. THE `MongoDBSource` SHALL parse URIs matching the `mongodb://` scheme.
2. THE source SHALL support optional certificate verification via the `verify_certificate` parameter.
3. IF the `pymongo` library is not installed, THE source SHALL raise an `ImportError` with a clear message.

---

### Requirement 8: Cryptography

**User Story:** As a developer, I want to encrypt and decrypt configuration content using Fernet symmetric encryption, so that sensitive configurations are protected.

#### Acceptance Criteria

1. THE `generate_fernet_key(keyphrase)` function SHALL generate a deterministic Fernet key from a keyphrase using `random.Random(keyphrase).randbytes(32)` encoded as URL-safe base64.
2. THE `encrypt_content(key, plain_content)` function SHALL encrypt a UTF-8 string using Fernet, returning a base64-encoded ciphertext string.
3. THE `decrypt_content(key, encrypted_content)` function SHALL decode the base64 ciphertext, decrypt with Fernet, and return the UTF-8 plaintext string.
4. THE `create_encrypted_configuration(key, plain_configuration, format?)` function SHALL return a dictionary with `"version": "1.0"`, `"format"`, and `"encrypted_content"` fields.

---

### Requirement 9: Configuration Variables

**User Story:** As a framework developer, I want a typed variable descriptor and accessor system for configuration settings, so that variables are resolved from environment, context, and defaults with proper type conversion.

#### Acceptance Criteria

1. THE `ConfigVariablesDesc` class SHALL extend `PersonaVariablesDesc` and define descriptors for all configuration variables using `AppVarDesc`.
2. FOR each configuration type (credentials, dataprofiles, landscape, topology, runtime), THE descriptors SHALL include: `_NAMES` (converter: `split_and_normalize_name_list`), `_FILES` (converter: `split_and_normalize_path_list`), `_SOURCES` (converter: `split_and_normalize_source_list`), `_URIS` (source: NONE), `REQUIRE_` (converter: `parse_bool`, default: False), `USE_` (source: NONE, default: False).
3. THE `ConfigVariables` class SHALL extend `PersonaVariables` and define accessors for all descriptors using `AppVarAccessor`.
4. THE `resolve_configuration_variables()` function SHALL resolve all descriptors via `ThisApplicationSingleton().resolve_variable_set(ConfigVariablesDesc)`, insert configuration maps into the application context (excluding credentials), and compute `USE_` flags based on whether names, files, or require flags are set for each type.
5. THE function SHALL be idempotent — guarded by `CONFIGURATION_VARIABLES_RESOLVED` flag.

---

### Requirement 10: Configuration Maps Resolution

**User Story:** As a framework developer, I want per-type configuration resolution that loads configs from sources and merges them into configuration maps, so that the application has a unified view of each configuration type.

#### Acceptance Criteria

1. THE `CONFIGURATION_MAPS` class SHALL maintain five `MergeMap` instances: `CREDENTIAL_CONFIGURATION_MAP`, `DATAPROFILE_CONFIGURATION_MAP`, `LANDSCAPE_CONFIGURATION_MAP`, `RUNTIME_CONFIGURATION_MAP` (initialized with `ConfigurationDefaults.DEFAULT_CONFIGURATION`), `TOPOLOGY_CONFIGURATION_MAP`.
2. THE `resolve_configuration_maps()` function SHALL accept optional `use_*` flags, `keyphrase`, and `credentials`, resolving each enabled type by calling its per-type resolution function.
3. FOR each configuration type, THE resolution function SHALL:
   a. Default to `"default-{type}"` config name if no names or files are specified.
   b. Default to `{config_directory}/{type_plural}` source path if names are specified but no sources.
   c. Create a `ConfigurationLoader` with the sources and load each named config, inserting into the type's `MergeMap` at position 0 (highest priority).
   d. Load each file config and insert into the `MergeMap`.
   e. Store the resolved URIs in the corresponding `_URIS` variable.

---

### Requirement 11: Input Normalization

**User Story:** As a framework developer, I want helper functions to normalize semicolon-separated input strings into typed lists, so that environment variable values are properly parsed.

#### Acceptance Criteria

1. THE `split_and_normalize_name_list(names_val, sep=";")` function SHALL split on the separator and strip whitespace from each name.
2. THE `split_and_normalize_path_list(paths_val, sep=";")` function SHALL split on the separator, strip `file://` prefixes, and expand each path using `os.path.abspath(os.path.expandvars(os.path.expanduser(...)))`.
3. THE `split_and_normalize_source_list(sources_val, sep=";")` function SHALL split on the separator and expand non-URI paths (those not starting with `http://`, `https://`, `dir://`, `mongodb://`, `couchdb://`) using the same path expansion.
4. THE default separator SHALL be `";"`.

---

### Requirement 12: Configuration Option Overrides

**User Story:** As a framework developer, I want static methods to override configuration names, sources, files, and requirements at runtime, so that CLI arguments and programmatic setup can control configuration loading.

#### Acceptance Criteria

1. THE `ConfigOptionOverrides` class SHALL provide static methods for each configuration type: `override_config_{type}_names`, `override_config_{type}_sources`, `override_config_{type}_files`.
2. WHEN overriding names or files, THE method SHALL also set the corresponding `REQUIRE_` flag to `True`.
3. WHEN overriding sources, THE method SHALL NOT set the require flag (sources alone don't imply requirement).
4. THE `override_configuration_requirements()` method SHALL accept boolean flags for each type and set the corresponding `REQUIRE_` variables.
5. ALL override methods SHALL use `ThisApplicationSingleton().override_variable_value()`.

---

### Requirement 13: Configuration Settings Establishment

**User Story:** As a framework developer, I want a one-time initialization function that establishes the application persona and default configuration, so that the configuration system is bootstrapped.

#### Acceptance Criteria

1. THE `establish_configuration_settings()` function SHALL accept optional `name`, `logger_name`, `log_basename`, `presence_dir`, `log_directory`, `settings_file`, `extensions`, `service_name`, and `default_configuration` parameters.
2. THE function SHALL be idempotent — guarded by `CONFIG_SETTINGS_ESTABLISHED` flag.
3. THE function SHALL call `establish_app_persona()` with the provided parameters.
4. IF `default_configuration` is provided, THE function SHALL replace `ConfigurationDefaults.DEFAULT_CONFIGURATION`.

---

### Requirement 14: Configuration Synchronization Base

**User Story:** As a framework developer, I want an abstract base for configuration synchronizers, so that new sync backends can be added.

#### Acceptance Criteria

1. THE `ConfigSynchronizerBase` SHALL accept a `storage_uri` and expose it as a property.
2. THE `try_publish(local_store, venue, user, config_name, credentials?)` method SHALL iterate over config classes (landscapes, topologies, runtimes, credentials), loading each from the local store and publishing to the remote store. Errors SHALL be collected and returned as a list of strings.
3. THE `try_retrieve(local_store, venue, user, config_name, credentials?)` method SHALL iterate over config classes, retrieving each from the remote store and saving locally. Errors SHALL be collected and returned.
4. THE `_save_local_config()` method SHALL create directories as needed and write the config in the specified format (JSON or YAML).
5. THE base SHALL define abstract methods: `_publish_configuration(venue, user, config_class, config_name, config_format, config_info, credentials)` and `_retrieve_configuration(venue, user, config_class, config_name, credentials) -> (format?, data?)`.
6. THE directory structure for synchronized configs SHALL be: `{storage_uri}/{venue}/{user}/{config_class}/{config_name}.{format}`.

---

### Requirement 15: Synchronization Backends

**User Story:** As a developer, I want multiple synchronization backends, so that configurations can be synced to different storage systems.

#### Acceptance Criteria

1. THE `DirectoryConfigSynchronizer` SHALL implement publish/retrieve using filesystem operations with the venue/user/class directory structure.
2. THE `CouchDBConfigSynchronizer` SHALL implement publish/retrieve using CouchDB document operations.
3. THE `MongoDBConfigSynchronizer` SHALL implement publish/retrieve using MongoDB collection operations.
4. THE `GithubConfigSynchronizer` SHALL implement publish/retrieve using GitHub repository API operations.
5. EACH backend SHALL handle its specific connection and authentication requirements.
6. EACH backend SHALL gracefully handle missing optional dependencies.

---

### Requirement 16: Default Values and Sentinels

**User Story:** As a framework developer, I want sentinel values for unset configuration fields, so that unset state is distinguishable from empty values.

#### Acceptance Criteria

1. THE `DefaultValues.NotSet` sentinel SHALL have the string value `"(not-set)"`.
2. THE sentinel SHALL be used to distinguish between "not configured" and "configured as empty".

---

### Requirement 17: Configuration Categories

**User Story:** As a developer, I want five distinct configuration categories with separate loading and merging, so that different types of configuration data are isolated.

#### Acceptance Criteria

1. THE system SHALL support five categories: Credentials, Landscapes, Topologies, Runtimes, Data Profiles.
2. EACH category SHALL have independent: names, files, sources, URIs, require flag, use flag, and MergeMap.
3. THE Runtime category SHALL be initialized with a default configuration containing version and logging levels.
4. THE Credentials category SHALL NOT be inserted into the application context (security protection).
5. ALL other categories SHALL be inserted into the application context via `ContextPaths`.

---

## Correctness Properties

- CP-1: For any configuration name present in at least one source, `load_configuration_by_name` returns the configuration from the first source in URI order.
- CP-2: For any keyphrase, `generate_fernet_key(keyphrase)` is deterministic — the same keyphrase always produces the same key.
- CP-3: For any plaintext and key, `decrypt_content(key, encrypt_content(key, plaintext)) == plaintext` (encryption round-trip).
- CP-4: `resolve_configuration_variables()` is idempotent — calling it multiple times has the same effect as calling it once.
- CP-5: For any configuration type, if `REQUIRE_` is True or names/files are set, then `USE_` is True after variable resolution.
- CP-6: Configuration maps merge with insertion at position 0, so later-loaded configs have higher priority.

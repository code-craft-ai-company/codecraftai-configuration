# AutoMojo Configuration Package Design Document

## Overview

The AutoMojo Configuration package is a comprehensive configuration management system designed for automation testing frameworks. It provides a flexible, multi-source configuration loading system with support for encryption, synchronization, and various storage backends.

## Architecture

### Core Components

The package follows a layered architecture with the following main components:

1. **Configuration Loader** - Central orchestrator for loading configurations
2. **Configuration Sources** - Pluggable backends for retrieving configurations  
3. **Configuration Synchronizers** - Components for publishing/retrieving configurations to/from remote stores
4. **Configuration Variables** - Environment variable management and resolution
5. **Cryptography Support** - Encryption/decryption capabilities for sensitive configurations
6. **Normalization Utilities** - Path and URI normalization functions

### Package Structure

```
ccai/configuration/
├── __init__.py
├── configurationloader.py          # Main configuration loading orchestrator
├── configurationsettings.py        # Application persona and settings establishment
├── configurationvariables.py       # Environment variable definitions and accessors
├── configurationmaps.py            # Configuration map resolution and management
├── configurationformat.py          # Supported configuration formats (JSON, YAML)
├── cryptography.py                 # Encryption/decryption utilities
├── normalize.py                    # Path and URI normalization functions
├── defaultvalues.py                # Sentinel values and defaults
├── optionoverrides.py              # Configuration override mechanisms
├── sources/                        # Configuration source implementations
│   ├── __init__.py
│   ├── configurationsourcebase.py  # Abstract base class for sources
│   ├── directorysource.py          # Local directory source
│   ├── httpsource.py               # HTTP/HTTPS source
│   ├── couchdbsource.py            # CouchDB source
│   └── mongodbsource.py            # MongoDB source
└── synchronization/                # Configuration synchronization components
    ├── __init__.py
    ├── configsynchronizerbase.py    # Abstract base class for synchronizers
    ├── directoryconfigsynchronizer.py
    ├── couchdbconfigsynchronizer.py
    ├── mongodbconfigsynchronizer.py
    └── githubconfigsynchronizer.py
```

## Design Patterns

### 1. Strategy Pattern
The configuration sources implement the Strategy pattern, allowing different backends (directory, HTTP, CouchDB, MongoDB) to be used interchangeably through a common interface (`ConfigurationSourceBase`).

### 2. Factory Pattern
The `ConfigurationLoader` acts as a factory, parsing URIs and instantiating appropriate source implementations based on URI schemes.

### 3. Template Method Pattern
The synchronization components use the Template Method pattern, with `ConfigSynchronizerBase` defining the overall synchronization workflow while allowing subclasses to implement specific storage operations.

### 4. Singleton Pattern
The application context uses a singleton pattern (`ThisApplicationSingleton`) to maintain global configuration state.

## Key Features

### Multi-Source Configuration Loading

The system supports loading configurations from multiple sources in priority order:

- **Directory Sources** (`dir://path`) - Local filesystem directories
- **HTTP Sources** (`http://` or `https://`) - Remote HTTP endpoints  
- **CouchDB Sources** (`couchdb://`) - CouchDB document databases
- **MongoDB Sources** (`mongodb://`) - MongoDB document databases

### Configuration Types

The system manages five distinct configuration categories:

1. **Credentials** - Authentication and access credentials
2. **Landscapes** - Environment and infrastructure definitions
3. **Topologies** - System topology and connectivity information
4. **Runtimes** - Runtime execution parameters
5. **Data Profiles** - Test data and data source configurations

### Encryption Support

Configurations can be encrypted using Fernet symmetric encryption:

- Key generation from passphrases
- Automatic encryption/decryption during load/save operations
- Support for encrypted configuration containers with metadata

### Format Support

The system supports multiple configuration file formats:

- **YAML** (`.yaml`, `.yml`) - Human-readable structured data
- **JSON** (`.json`) - Machine-readable structured data

### Environment Variable Integration

Comprehensive environment variable system with:

- Automatic variable resolution and type conversion
- Context-aware variable scoping
- Override mechanisms for runtime customization
- Default value management

## Component Details

### ConfigurationLoader

The central orchestrator responsible for:

- Parsing and validating source URIs
- Instantiating appropriate source implementations
- Coordinating multi-source configuration searches
- Handling encryption/decryption operations
- Managing credentials for authenticated sources

**Key Methods:**
- `load_configuration_by_name()` - Search sources for named configuration
- `load_configuration_from_file()` - Direct file loading with encryption support

### Configuration Sources

Abstract base class `ConfigurationSourceBase` defines the contract:

```python
@abstractmethod
def try_load_configuration(self, config_name: str) -> Union[Tuple[ConfigurationFormat, dict], Tuple[None, None]]
```

**Implementations:**

- **DirectorySource** - Searches local directories for configuration files
- **HttpSource** - Retrieves configurations from HTTP/HTTPS endpoints
- **CouchDBSource** - Loads configurations from CouchDB documents
- **MongoDBSource** - Retrieves configurations from MongoDB collections

### Configuration Synchronizers

Enable bidirectional synchronization between local and remote configuration stores:

- **Publishing** - Upload local configurations to remote stores
- **Retrieval** - Download configurations from remote stores to local filesystem
- **Multi-format support** - Handle both JSON and YAML formats
- **Namespace management** - Organize configurations by venue/user/class

### Variable Management

The configuration variable system provides:

- **Descriptors** (`ConfigVariablesDesc`) - Define variable metadata and behavior
- **Accessors** (`ConfigVariables`) - Provide runtime access to variable values
- **Resolution** - Automatic environment variable processing and normalization
- **Context Integration** - Variables are automatically inserted into application context

### Cryptography

Encryption capabilities include:

- **Key Generation** - Deterministic key generation from passphrases
- **Content Encryption** - Symmetric encryption using Fernet algorithm
- **Transparent Operations** - Automatic encrypt/decrypt during configuration operations
- **Metadata Preservation** - Encrypted configurations retain format and version information

## Usage Patterns

### Basic Configuration Loading

```python
# Initialize loader with source URIs
loader = ConfigurationLoader([
    "dir:///path/to/configs",
    "https://config-server.example.com/configs"
])

# Load configuration by name
config_uri, config_data = loader.load_configuration_by_name("my-config")
```

### Encrypted Configuration Handling

```python
# Load encrypted configuration with passphrase
config_uri, config_data = loader.load_configuration_by_name(
    "secure-config", 
    keyphrase="my-secret-phrase"
)
```

### Multi-Type Configuration Resolution

```python
# Resolve all configuration types
resolve_configuration_maps(
    use_credentials=True,
    use_landscape=True,
    use_topology=True,
    use_runtime=True,
    keyphrase="encryption-key"
)
```

## Security Considerations

### Credential Protection

- Credentials are not stored in application context by default
- Encrypted storage support for sensitive configurations
- Secure key derivation from passphrases

### Certificate Validation

- HTTPS certificate verification enabled by default
- Configurable certificate validation for development environments

### Access Control

- URI-based access control through source configuration
- Credential mapping for authenticated sources
- Namespace isolation in synchronized configurations

## Extensibility

### Adding New Sources

New configuration sources can be added by:

1. Extending `ConfigurationSourceBase`
2. Implementing required abstract methods
3. Registering URI scheme in `ConfigurationLoader`

### Custom Synchronizers

New synchronization backends can be added by:

1. Extending `ConfigSynchronizerBase`
2. Implementing publish/retrieve operations
3. Adding URI parsing logic

### Format Extensions

Additional configuration formats can be supported by:

1. Extending `ConfigurationFormat` enumeration
2. Adding format detection logic
3. Implementing serialization/deserialization

## Dependencies

### Core Dependencies

- **PyYAML** - YAML format support
- **requests** - HTTP source implementation
- **cryptography** - Encryption/decryption operations

### Optional Dependencies

- **pymongo** - MongoDB source support
- **couchdb** - CouchDB source integration

### Internal Dependencies

- **ccai.errors** - Exception handling
- **ccai.thisapp** - Application context and variable management
- **ccai.xmodules** - Extended utility modules

## Performance Considerations

### Caching Strategy

- Configuration maps use merge semantics for efficient layering
- Source instances are cached within loader lifecycle
- Variable resolution is performed once during initialization

### Network Optimization

- HTTP sources support connection reuse
- Database sources maintain persistent connections
- Configurable timeouts and retry logic

### Memory Management

- Lazy loading of configuration data
- Efficient merge operations for configuration layering
- Minimal memory footprint for unused configuration types

## Error Handling

### Graceful Degradation

- Missing configurations return `None` rather than raising exceptions
- Source failures are isolated and don't affect other sources
- Comprehensive error reporting with source context

### Validation

- URI format validation during source initialization
- Configuration format validation during loading
- Type checking for environment variables

### Debugging Support

- Detailed error messages with source context
- Configuration URI tracking for audit trails
- Verbose logging support for troubleshooting

## Future Enhancements

### Planned Features

1. **Configuration Validation** - Schema-based validation for loaded configurations
2. **Hot Reloading** - Dynamic configuration updates without restart
3. **Audit Logging** - Comprehensive audit trail for configuration access
4. **Configuration Templating** - Template-based configuration generation
5. **Distributed Caching** - Shared configuration cache across instances

### Architectural Improvements

1. **Async Support** - Asynchronous configuration loading for improved performance
2. **Plugin Architecture** - Dynamic plugin loading for sources and synchronizers
3. **Configuration Versioning** - Version control integration for configuration management
4. **Health Monitoring** - Built-in health checks for configuration sources

This design document reflects the current state of the AutoMojo Configuration package as implemented in the source code, providing a comprehensive overview of its architecture, features, and usage patterns.
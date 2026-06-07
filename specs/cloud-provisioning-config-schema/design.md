# Design

## Overview

This module is the config-layer entry point for cloud provisioning specs.  It owns
the YAML fragment definitions, the top-level loader function, and the binding to the
`SchemaObject`-based model classes in `codecraftai-provisioning`.  Schema validation
delegates to the model classes' own `from_dict` — the fragments here only describe
the *outer shape* (which keys exist, how they nest) and the registration that wires
each key to its model.

The decision to keep the schema in `codecraftai-configuration` instead of inside
`codecraftai-provisioning` follows the project's existing pattern: every consumer that
loads landscape, profile, or environment YAML uses the same loader and validator,
and provisioning is no different.

---

## Architecture

```
   user YAML file
        │
        ▼
   load_cloud_provisioning_config(path)
        │
        │ yaml.safe_load
        ▼
   raw dict
        │
        │ for each top-level key:
        │   look up registered fragment
        │   call fragment.parse(payload[key]) -> List[ModelObject]
        ▼
   CloudProvisioningConfig (typed aggregate)
        │
        ▼
   consumed by codecraftai-provisioning.ProvisioningEngine
```

---

## Data Model

```python
class CloudProvisioningConfig(SchemaObject):
    networks:           List[CloudNetwork]
    subnets:            List[CloudSubnet]
    security_groups:    List[CloudSecurityGroup]
    keypairs:           List[CloudKeyPair]
    accelerators:       List[CloudAcceleratorAssignment]
    shared_filesystems: List[CloudSharedFilesystem]
    venues:             List[Union[CloudVenue, WorkloadVenue]]
    devices:            List[CloudInstance]                      # devices[*].vpn_join lives here


class CloudAcceleratorAssignment(SchemaObject):
    """Per-instance accelerator declarations parsed from the accelerators block."""
    instance_name: str
    accelerators: List[CloudAcceleratorSpec]


class CloudProvisioningSchemaFragment(SchemaObject):
    key: str                       # top-level YAML key
    model_class: type              # SchemaObject subclass used to parse entries
    required: bool = False


def load_cloud_provisioning_config(*, path: str) -> CloudProvisioningConfig: ...

def validate_cloud_provisioning_config(*, payload: dict) -> None: ...

def register_cloud_provisioning_fragments() -> None:
    """Called at module import; registers fragments with the global loader."""
    ...
```

---

## Registered Fragments

| Key                  | Parses into                        | Required |
| -------------------- | ---------------------------------- | -------- |
| `networks`           | `List[CloudNetwork]`               | no       |
| `subnets`            | `List[CloudSubnet]`                | no       |
| `security_groups`    | `List[CloudSecurityGroup]`         | no       |
| `keypairs`           | `List[CloudKeyPair]`               | no       |
| `accelerators`       | `List[CloudAcceleratorAssignment]` | no       |
| `shared_filesystems` | `List[CloudSharedFilesystem]`      | no       |
| `venues`             | `List[CloudVenue|WorkloadVenue]`   | yes      |
| `devices`            | `List[CloudInstance]`              | yes      |
| `vpn`                | `Dict[str, Any]` (delegates)       | no       |

Per-device `vpn_join` is a nested sub-block on each `devices` entry, not a top-level
fragment.

---

## YAML Sketch

```yaml
networks:
  - name: lab-vpc
    cidr: 10.0.0.0/16
    region: us-east-1
    tags:
      - env: ci

subnets:
  - name: lab-subnet-a
    network: lab-vpc
    cidr: 10.0.1.0/24
    zone: us-east-1a
    public: true

security_groups:
  - name: lab-web
    network: lab-vpc
    ingress_rules:
      - protocol: tcp
        from_port: 22
        to_port: 22
        source_cidrs: ["0.0.0.0/0"]
        description: ssh

accelerators:
  - instance_name: trainer-01
    accelerators:
      - kind: GPU
        model: H100_SXM
        count: 8
        interconnect: NVSWITCH
        memory_gb: 80

devices:
  - name: web-01
    profile_ref: web
    image: { family: ubuntu, version: "24.04", architecture: x86_64 }
    size: small
    subnet: lab-subnet-a
    security_groups: [lab-web]
    keypair: lab-key
    public_ip: true
    vpn_join:
      provider: tailscale
      control_plane_credential: tailscale-oauth-lab
      advertise_tags: ["tag:lab"]
      hostname_template: "{venue}-{group}-{index}"
    preemption_policy: FAIL
```

---

## Module Layout

```
source/packages/ccai/configuration/cloudprovisioning/
├── cloudprovisioningconfig.py
├── cloudacceleratorassignment.py
├── cloudprovisioningfragment.py
├── cloudprovisioningloader.py        # load_cloud_provisioning_config
└── cloudprovisioningvalidator.py     # validate_cloud_provisioning_config
```

---

## See Also

- [cloud-resource-model](../../../codecraftai-provisioning/specs/cloud-resource-model/design.md)
- [accelerator-and-interconnect-model](../../../codecraftai-provisioning/specs/accelerator-and-interconnect-model/design.md)
- [accelerator-catalog](../../../codecraftai-provisioning/specs/accelerator-catalog/design.md)
- [vpn-join-spec](../../../codecraftai-provisioning/specs/vpn-join-spec/design.md)
- [provisioning-engine-pipeline](../../../codecraftai-provisioning/specs/provisioning-engine-pipeline/design.md)
- [workload-provisioning-config-schema](../workload-provisioning-config-schema/design.md)
- existing `codecraftai-configuration` loader contract (referenced from the config root spec)

---

## Testing Strategy

- **Unit tests** — load every example fragment from a fixtures directory; assert
  the typed aggregate carries the expected lists.
- **Missing-key tests** — absent top-level keys default to empty lists.
- **Bad-shape tests** — malformed nested objects raise `ConfigurationError` with
  the YAML path.
- **Cross-reference tests** — `accelerators` entry referencing an unknown
  `instance_name` raises `ConfigurationError`.
- **Override pass-through test** — venue override map appears verbatim on the
  resulting venue object.
- No property tests required at this layer — the heavy invariants live in the
  model and lifecycle specs in `codecraftai-provisioning`.

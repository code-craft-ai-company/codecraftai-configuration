# Design

## Overview

This module is the configuration entry point for workload-shaped provisioning specs.
It mirrors the cloud-side schema module exactly: fragment definitions for each
top-level key, a typed aggregate, and load + validate functions.

Workload and cloud blocks routinely co-exist in the same YAML file.  Both loaders
operate on the same dict and produce two typed aggregates; the engine pipeline
consumes both.  Co-existence is the common case for self-hosted K8s on AWS-style
deployments.

---

## Architecture

```
   user YAML file (may include both cloud and workload blocks)
        │
        ▼
   load_workload_provisioning_config(path)
        │
        │ yaml.safe_load
        ▼
   raw dict
        │
        │ for each workload top-level key:
        │   look up registered fragment
        │   call fragment.parse(payload[key]) -> List[ModelObject]
        ▼
   WorkloadProvisioningConfig (typed aggregate)
        │
        ▼
   consumed by codecraftai-provisioning.ProvisioningEngine
        (alongside the parallel CloudProvisioningConfig)
```

---

## Data Model

```python
class WorkloadProvisioningConfig(SchemaObject):
    workload_venues:    List[WorkloadVenue]
    workload_clusters:  List[WorkloadCluster]
    workload_jobs:      List[WorkloadJob]
    workload_services:  List[WorkloadService]


class WorkloadProvisioningSchemaFragment(SchemaObject):
    key: str
    model_class: type
    required: bool = False


def load_workload_provisioning_config(*, path: str) -> WorkloadProvisioningConfig: ...

def validate_workload_provisioning_config(*, payload: dict) -> None: ...

def register_workload_provisioning_fragments() -> None: ...
```

---

## Registered Fragments

| Key                  | Parses into             |
| -------------------- | ----------------------- |
| `workload_venues`    | `List[WorkloadVenue]`   |
| `workload_clusters`  | `List[WorkloadCluster]` |
| `workload_jobs`      | `List[WorkloadJob]`     |
| `workload_services`  | `List[WorkloadService]` |

---

## YAML Sketch

```yaml
workload_venues:
  - name: lab-coreweave
    kind: KUBERNETES
    credential_ref: coreweave-lab
    tags:
      - env: lab

  - name: future-slurm
    kind: SLURM                          # accepted; apply NIE in v1
    credential_ref: slurm-cluster-creds

workload_clusters:
  - name: training-cluster
    node_pools:
      - name: cpu-pool
        count: 3
        size: m5.large
        taints: []
        labels: { pool: cpu }
    accelerator_pools:
      - name: h100-pool
        count: 4
        size: a3-highgpu-8g
        accelerators:
          - kind: GPU
            model: H100_SXM
            count: 8
            interconnect: NVSWITCH
            memory_gb: 80
        interconnect:
          kind: INFINIBAND_NDR
          bandwidth_gbps: 3200
          topology: RAIL_OPTIMIZED
        taints: []
        labels: { pool: h100 }
    autoscaling:
      min_nodes: 1
      max_nodes: 32
      target_utilisation: 0.75
    networking: {}

workload_jobs:
  - name: train-llm
    image: ghcr.io/lab/trainer:1.2
    command: ["python", "train.py"]
    resources: { cpu: 8, memory: "64Gi" }
    accelerators:
      - kind: GPU
        model: H100_SXM
        count: 8
        interconnect: NVSWITCH
        memory_gb: 80
    replicas: 1
    restart_policy: Never
    env: { WANDB_PROJECT: lab }
    network: training-net

workload_services:
  - name: inference-endpoint
    image: ghcr.io/lab/inference:1.0
    command: ["python", "serve.py"]
    resources: { cpu: 2, memory: "8Gi" }
    accelerators:
      - kind: GPU
        model: L40S
        count: 1
        interconnect: PCIE
        memory_gb: 48
    replicas: 2
    ports:
      - { name: http, containerPort: 8080, protocol: TCP }
    env: { MODEL: llama3-8b }
    exposure: LoadBalancer
```

---

## Composition with Cloud

`workload_venues[*]` may include a `cloud_provisioner_ref: str` field naming a
`CloudVenue` from the same file's `venues:` block.  When present, the engine drives
the cloud venue's `apply` before the workload venue's `apply` and reverses on
destroy.  This is the path for self-hosted K8s on cloud infrastructure.

---

## Module Layout

```
source/packages/ccai/configuration/workloadprovisioning/
├── workloadprovisioningconfig.py
├── workloadprovisioningfragment.py
├── workloadprovisioningloader.py
└── workloadprovisioningvalidator.py
```

---

## See Also

- [workload-venue-model](../../../codecraftai-provisioning/specs/workload-venue-model/design.md)
- [accelerator-and-interconnect-model](../../../codecraftai-provisioning/specs/accelerator-and-interconnect-model/design.md)
- [accelerator-catalog](../../../codecraftai-provisioning/specs/accelerator-catalog/design.md)
- [cloud-provisioning-config-schema](../cloud-provisioning-config-schema/design.md)
- [provisioning-engine-pipeline](../../../codecraftai-provisioning/specs/provisioning-engine-pipeline/design.md)

---

## Testing Strategy

- **Unit tests** — load a fixture YAML containing every block; assert the typed
  aggregate carries the expected lists.
- **Missing-key tests** — absent blocks default to empty lists.
- **Bad-shape tests** — malformed nested objects raise `ConfigurationError` with
  the YAML path identified.
- **Enum-rejection tests** — unknown `kind` / `exposure` / `restart_policy` raise
  `ConfigurationError`.
- **Catalog cross-reference test** — node-pool accelerator referencing a model not
  in the catalog raises `ConfigurationError`.
- **Composition test** — `cloud_provisioner_ref` pointing to an unknown venue
  raises `ConfigurationError`; valid ref passes through to the typed aggregate.
- **Co-existence test** — load a single file with both cloud and workload blocks
  via both loaders; assert both aggregates are consistent.
- No property tests required at this layer.

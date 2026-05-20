"""
.. module:: workloadprovisioningconfigschema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Schema fragments for the workload-provisioning top-level
        blocks (``workload_venues``, ``workload_clusters``,
        ``workload_jobs``, ``workload_services``).

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from automojo.errors.exceptions import ConfigurationError

from automojo.configuration.schemas.cloudprovisioningconfigschema import (
    CloudVenueOverrides,
)


# ---------------------------------------------------------------------------
# Cross-repository type fallbacks.
#
# The canonical workload models live in ``automojo-provisioning`` (Phase 1a).
# Until those packages land this module uses lightweight local fallbacks.
# ---------------------------------------------------------------------------

try:
    from automojo.provisioning.models.workloadvenuekind import (  # type: ignore
        WORKLOAD_VENUE_KINDS,
    )
except ImportError:
    WORKLOAD_VENUE_KINDS: Tuple[str, ...] = (
        "kubernetes", "slurm", "ray", "nomad",
    )


IMPLEMENTED_WORKLOAD_VENUE_KINDS: Tuple[str, ...] = ("kubernetes",)

NOT_IMPLEMENTED_V1_KINDS: Tuple[str, ...] = ("slurm", "ray", "nomad")

SUPPORTED_RESTART_POLICIES: Tuple[str, ...] = ("Never", "OnFailure")

SUPPORTED_EXPOSURES: Tuple[str, ...] = ("ClusterIP", "LoadBalancer", "NodePort")


# ---------------------------------------------------------------------------
# Dataclasses for each top-level block entry.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkloadAcceleratorRequest:
    """
        Typed representation of an accelerator request on a job, service or
        node pool.

        :param kind: Accelerator kind (e.g. ``GPU``).
        :param model: Catalog model identifier (e.g. ``H100_SXM``).
        :param count: Number of devices required.
        :param interconnect: Optional interconnect technology.
        :param memory_gb: Optional per-device memory in GB.
    """
    kind: str
    model: str
    count: int
    interconnect: Optional[str] = None
    memory_gb: Optional[int] = None


@dataclass(frozen=True)
class WorkloadNodePoolSpec:
    """
        Typed representation of a node-pool entry.

        :param name: Pool identifier.
        :param count: Static pool size.
        :param size: Provider-neutral instance size token.
        :param accelerators: Optional accelerator requests for the pool.
        :param taints: List of taint dicts.
        :param labels: Label dict applied to nodes in the pool.
    """
    name: str
    count: int
    size: str
    accelerators: List[WorkloadAcceleratorRequest] = field(default_factory=list)
    taints: List[Dict[str, Any]] = field(default_factory=list)
    labels: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkloadVenueSpec:
    """
        Typed representation of a ``workload_venues[*]`` entry.

        :param name: Unique venue identifier.
        :param kind: One of ``kubernetes``, ``slurm``, ``ray``, ``nomad``.
        :param credential_ref: Identifier of the credential used to talk to
            the venue's control plane.
        :param cloud_provisioner_ref: Optional name of a cloud venue from
            the same spec that must be provisioned first.
        :param tags: Optional list of single-key tag dicts.
    """
    name: str
    kind: str
    credential_ref: str
    cloud_provisioner_ref: Optional[str] = None
    tags: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class WorkloadClusterSpec:
    """
        Typed representation of a ``workload_clusters[*]`` entry.

        :param name: Cluster identifier.
        :param venue: Name of the parent workload venue.
        :param node_pools: Standard node pools.
        :param accelerator_pools: Accelerator-bearing node pools.
    """
    name: str
    venue: str
    node_pools: List[WorkloadNodePoolSpec] = field(default_factory=list)
    accelerator_pools: List[WorkloadNodePoolSpec] = field(default_factory=list)


@dataclass(frozen=True)
class WorkloadSharedFsMount:
    """
        Typed representation of a shared-filesystem mount.

        :param filesystem_name: Identifier of a declared shared filesystem.
        :param mount_path: Path inside the workload container.
        :param read_only: ``True`` to mount read-only.
    """
    filesystem_name: str
    mount_path: str
    read_only: bool = False


@dataclass(frozen=True)
class WorkloadJobSpec:
    """
        Typed representation of a ``workload_jobs[*]`` entry.

        :param name: Job identifier.
        :param venue: Name of the parent workload venue.
        :param image: Container image reference.
        :param command: Container entrypoint command.
        :param resources: Resource request dict (cpu, memory, ...).
        :param accelerators: Optional accelerator requests.
        :param replicas: Number of replicas to launch.
        :param restart_policy: One of ``Never``, ``OnFailure``.
        :param env: Environment variable dict.
        :param shared_fs_mounts: Shared-filesystem mount declarations.
    """
    name: str
    venue: str
    image: str
    command: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    accelerators: List[WorkloadAcceleratorRequest] = field(default_factory=list)
    replicas: int = 1
    restart_policy: str = "Never"
    env: Dict[str, Any] = field(default_factory=dict)
    shared_fs_mounts: List[WorkloadSharedFsMount] = field(default_factory=list)


@dataclass(frozen=True)
class WorkloadServiceSpec:
    """
        Typed representation of a ``workload_services[*]`` entry.

        :param name: Service identifier.
        :param venue: Name of the parent workload venue.
        :param image: Container image reference.
        :param command: Container entrypoint command.
        :param resources: Resource request dict.
        :param accelerators: Optional accelerator requests.
        :param replicas: Number of replicas to launch.
        :param ports: List of port dicts.
        :param env: Environment variable dict.
        :param exposure: One of ``ClusterIP``, ``LoadBalancer``, ``NodePort``.
    """
    name: str
    venue: str
    image: str
    command: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    accelerators: List[WorkloadAcceleratorRequest] = field(default_factory=list)
    replicas: int = 1
    ports: List[Dict[str, Any]] = field(default_factory=list)
    env: Dict[str, Any] = field(default_factory=dict)
    exposure: str = "ClusterIP"


@dataclass(frozen=True)
class WorkloadProvisioningBlock:
    """
        Typed aggregate of every workload-provisioning block.

        :param workload_venues: Parsed venues.
        :param workload_clusters: Parsed clusters.
        :param workload_jobs: Parsed jobs.
        :param workload_services: Parsed services.
    """
    workload_venues: List[WorkloadVenueSpec] = field(default_factory=list)
    workload_clusters: List[WorkloadClusterSpec] = field(default_factory=list)
    workload_jobs: List[WorkloadJobSpec] = field(default_factory=list)
    workload_services: List[WorkloadServiceSpec] = field(default_factory=list)


CredentialLookup = Callable[[str], Optional[Any]]


# ---------------------------------------------------------------------------
# Validation helpers.
# ---------------------------------------------------------------------------

def _require_mapping(*, entry: Any, path: str, err_lines: List[str]) -> bool:
    if not isinstance(entry, dict):
        err_lines.append(f"{path} must be a mapping.")
        rtnval = False
        return rtnval
    rtnval = True
    return rtnval


def _require_keys(*, entry: dict, required: Tuple[str, ...], path: str,
                  err_lines: List[str]) -> bool:
    missing: List[str] = []
    for key in required:
        if key not in entry:
            missing.append(key)
    if len(missing) > 0:
        err_lines.append(
            f"{path} missing required keys: {missing!r}."
        )
        rtnval = False
        return rtnval
    rtnval = True
    return rtnval


def _validate_enum(*, raw: Any, accepted: Tuple[str, ...], path: str,
                   err_lines: List[str]) -> Optional[str]:
    if raw not in accepted:
        err_lines.append(
            f"{path}={raw!r} must be one of {list(accepted)!r}."
        )
        rtnval = None
        return rtnval
    rtnval = raw
    return rtnval


def _raise_if_errors(*, label: str, err_lines: List[str]) -> None:
    if len(err_lines) == 0:
        return
    msg_lines = [
        f"workload-provisioning-config-schema validation failed in {label}:"
    ]
    for line in err_lines:
        msg_lines.append("  - " + line)
    err_msg = os.linesep.join(msg_lines)
    raise ConfigurationError(err_msg)


def _parse_accelerator_requests(*, raw: Any, path: str,
                                err_lines: List[str]
                                ) -> List[WorkloadAcceleratorRequest]:
    rtnval: List[WorkloadAcceleratorRequest] = []
    if raw is None:
        return rtnval
    if not isinstance(raw, list):
        err_lines.append(f"{path} must be a list.")
        return rtnval
    for idx, entry in enumerate(raw):
        item_path = f"{path}[{idx}]"
        if not _require_mapping(
            entry=entry, path=item_path, err_lines=err_lines
        ):
            continue
        if not _require_keys(
            entry=entry,
            required=("kind", "model", "count"),
            path=item_path,
            err_lines=err_lines,
        ):
            continue
        req = WorkloadAcceleratorRequest(
            kind=entry["kind"],
            model=entry["model"],
            count=int(entry["count"]),
            interconnect=entry.get("interconnect"),
            memory_gb=entry.get("memory_gb"),
        )
        rtnval.append(req)
    return rtnval


# ---------------------------------------------------------------------------
# Per-block loaders.
# ---------------------------------------------------------------------------

def load_workload_venues_block(*, data: Optional[list] = None,
                               cloud_venues: Optional[List[CloudVenueOverrides]] = None,
                               credential_lookup: Optional[CredentialLookup] = None
                               ) -> List[WorkloadVenueSpec]:
    """
        Parses and validates the ``workload_venues:`` block.

        :param data: The raw list value of the ``workload_venues:`` key.
        :param cloud_venues: Already-parsed cloud venues for
            ``cloud_provisioner_ref`` cross-reference.
        :param credential_lookup: Optional callable resolving
            ``credential_ref`` identifiers.

        :returns: List of parsed ``WorkloadVenueSpec``.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    cloud_venues_ref = cloud_venues if cloud_venues is not None else []
    rtnval = _parse_workload_venues(
        data=data,
        cloud_venues=cloud_venues_ref,
        credential_lookup=credential_lookup,
        err_lines=err_lines,
    )
    _raise_if_errors(label="workload_venues", err_lines=err_lines)
    return rtnval


def _parse_workload_venues(*, data: Optional[list],
                           cloud_venues: List[CloudVenueOverrides],
                           credential_lookup: Optional[CredentialLookup],
                           err_lines: List[str]
                           ) -> List[WorkloadVenueSpec]:
    rtnval: List[WorkloadVenueSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("workload_venues must be a list.")
        return rtnval
    known_cloud = {v.name for v in cloud_venues}
    for idx, entry in enumerate(raw_list):
        path = f"workload_venues[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "kind", "credential_ref"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        kind_raw = entry["kind"]
        kind_normalised = (
            kind_raw.lower() if isinstance(kind_raw, str) else kind_raw
        )
        kind = _validate_enum(
            raw=kind_normalised,
            accepted=WORKLOAD_VENUE_KINDS,
            path=f"{path}.kind",
            err_lines=err_lines,
        )
        if kind is None:
            continue
        cred_ref = entry["credential_ref"]
        if credential_lookup is not None:
            resolved = credential_lookup(cred_ref)
            if resolved is None:
                err_lines.append(
                    f"{path}.credential_ref={cred_ref!r} did not resolve "
                    f"to any known credential identifier."
                )
                continue
        cloud_ref = entry.get("cloud_provisioner_ref")
        if cloud_ref is not None and cloud_ref not in known_cloud:
            err_lines.append(
                f"{path}.cloud_provisioner_ref={cloud_ref!r} does not "
                f"reference any declared cloud venue."
            )
            continue
        spec = WorkloadVenueSpec(
            name=entry["name"],
            kind=kind,
            credential_ref=cred_ref,
            cloud_provisioner_ref=cloud_ref,
            tags=list(entry.get("tags", [])),
        )
        rtnval.append(spec)
    return rtnval


def load_workload_clusters_block(*, data: Optional[list] = None,
                                 venues: Optional[List[WorkloadVenueSpec]] = None
                                 ) -> List[WorkloadClusterSpec]:
    """
        Parses and validates the ``workload_clusters:`` block.

        :param data: The raw list value of the ``workload_clusters:`` key.
        :param venues: Already-parsed workload venues for cross-reference.

        :returns: List of parsed ``WorkloadClusterSpec``.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    venues_ref = venues if venues is not None else []
    rtnval = _parse_workload_clusters(
        data=data, venues=venues_ref, err_lines=err_lines
    )
    _raise_if_errors(label="workload_clusters", err_lines=err_lines)
    return rtnval


def _parse_workload_clusters(*, data: Optional[list],
                             venues: List[WorkloadVenueSpec],
                             err_lines: List[str]
                             ) -> List[WorkloadClusterSpec]:
    rtnval: List[WorkloadClusterSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("workload_clusters must be a list.")
        return rtnval
    known_venues = {v.name for v in venues}
    for idx, entry in enumerate(raw_list):
        path = f"workload_clusters[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "venue"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        venue_name = entry["venue"]
        if len(known_venues) > 0 and venue_name not in known_venues:
            err_lines.append(
                f"{path}.venue={venue_name!r} does not reference any "
                f"declared workload_venues[*].name."
            )
            continue
        node_pools = _parse_node_pools(
            raw=entry.get("node_pools", []),
            path=f"{path}.node_pools",
            err_lines=err_lines,
        )
        accelerator_pools = _parse_node_pools(
            raw=entry.get("accelerator_pools", []),
            path=f"{path}.accelerator_pools",
            err_lines=err_lines,
        )
        spec = WorkloadClusterSpec(
            name=entry["name"],
            venue=venue_name,
            node_pools=node_pools,
            accelerator_pools=accelerator_pools,
        )
        rtnval.append(spec)
    return rtnval


def _parse_node_pools(*, raw: Any, path: str,
                      err_lines: List[str]) -> List[WorkloadNodePoolSpec]:
    rtnval: List[WorkloadNodePoolSpec] = []
    if not isinstance(raw, list):
        err_lines.append(f"{path} must be a list.")
        return rtnval
    for idx, entry in enumerate(raw):
        item_path = f"{path}[{idx}]"
        if not _require_mapping(
            entry=entry, path=item_path, err_lines=err_lines
        ):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "count", "size"),
            path=item_path,
            err_lines=err_lines,
        ):
            continue
        accelerators = _parse_accelerator_requests(
            raw=entry.get("accelerators"),
            path=f"{item_path}.accelerators",
            err_lines=err_lines,
        )
        pool = WorkloadNodePoolSpec(
            name=entry["name"],
            count=int(entry["count"]),
            size=entry["size"],
            accelerators=accelerators,
            taints=list(entry.get("taints", [])),
            labels=dict(entry.get("labels", {})),
        )
        rtnval.append(pool)
    return rtnval


def load_workload_jobs_block(*, data: Optional[list] = None,
                             venues: Optional[List[WorkloadVenueSpec]] = None,
                             shared_filesystem_names: Optional[List[str]] = None
                             ) -> List[WorkloadJobSpec]:
    """
        Parses and validates the ``workload_jobs:`` block.

        :param data: The raw list value of the ``workload_jobs:`` key.
        :param venues: Already-parsed workload venues for cross-reference.
        :param shared_filesystem_names: Names of declared shared
            filesystems used to validate ``shared_fs_mounts``.

        :returns: List of parsed ``WorkloadJobSpec``.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    venues_ref = venues if venues is not None else []
    fs_names = shared_filesystem_names if shared_filesystem_names is not None else []
    rtnval = _parse_workload_jobs(
        data=data,
        venues=venues_ref,
        shared_filesystem_names=fs_names,
        err_lines=err_lines,
    )
    _raise_if_errors(label="workload_jobs", err_lines=err_lines)
    return rtnval


def _parse_workload_jobs(*, data: Optional[list],
                         venues: List[WorkloadVenueSpec],
                         shared_filesystem_names: List[str],
                         err_lines: List[str]) -> List[WorkloadJobSpec]:
    rtnval: List[WorkloadJobSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("workload_jobs must be a list.")
        return rtnval
    known_venues = {v.name for v in venues}
    known_fs = set(shared_filesystem_names)
    for idx, entry in enumerate(raw_list):
        path = f"workload_jobs[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "venue", "image"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        venue_name = entry["venue"]
        if len(known_venues) > 0 and venue_name not in known_venues:
            err_lines.append(
                f"{path}.venue={venue_name!r} does not reference any "
                f"declared workload_venues[*].name."
            )
            continue
        restart_policy = entry.get("restart_policy", "Never")
        policy = _validate_enum(
            raw=restart_policy,
            accepted=SUPPORTED_RESTART_POLICIES,
            path=f"{path}.restart_policy",
            err_lines=err_lines,
        )
        if policy is None:
            continue
        replicas = int(entry.get("replicas", 1))
        if replicas <= 0:
            err_lines.append(
                f"{path}.replicas={replicas} must be greater than 0."
            )
            continue
        accelerators = _parse_accelerator_requests(
            raw=entry.get("accelerators"),
            path=f"{path}.accelerators",
            err_lines=err_lines,
        )
        mounts = _parse_shared_fs_mounts(
            raw=entry.get("shared_fs_mounts", []),
            path=f"{path}.shared_fs_mounts",
            known_fs=known_fs,
            err_lines=err_lines,
        )
        spec = WorkloadJobSpec(
            name=entry["name"],
            venue=venue_name,
            image=entry["image"],
            command=list(entry.get("command", [])),
            resources=dict(entry.get("resources", {})),
            accelerators=accelerators,
            replicas=replicas,
            restart_policy=policy,
            env=dict(entry.get("env", {})),
            shared_fs_mounts=mounts,
        )
        rtnval.append(spec)
    return rtnval


def _parse_shared_fs_mounts(*, raw: Any, path: str,
                            known_fs: set,
                            err_lines: List[str]
                            ) -> List[WorkloadSharedFsMount]:
    rtnval: List[WorkloadSharedFsMount] = []
    if not isinstance(raw, list):
        err_lines.append(f"{path} must be a list.")
        return rtnval
    for idx, entry in enumerate(raw):
        item_path = f"{path}[{idx}]"
        if not _require_mapping(
            entry=entry, path=item_path, err_lines=err_lines
        ):
            continue
        if not _require_keys(
            entry=entry,
            required=("filesystem_name", "mount_path"),
            path=item_path,
            err_lines=err_lines,
        ):
            continue
        fs_name = entry["filesystem_name"]
        if len(known_fs) > 0 and fs_name not in known_fs:
            err_lines.append(
                f"{item_path}.filesystem_name={fs_name!r} does not reference "
                f"any declared shared filesystem."
            )
            continue
        mount = WorkloadSharedFsMount(
            filesystem_name=fs_name,
            mount_path=entry["mount_path"],
            read_only=bool(entry.get("read_only", False)),
        )
        rtnval.append(mount)
    return rtnval


def load_workload_services_block(*, data: Optional[list] = None,
                                 venues: Optional[List[WorkloadVenueSpec]] = None
                                 ) -> List[WorkloadServiceSpec]:
    """
        Parses and validates the ``workload_services:`` block.

        :param data: The raw list value of the ``workload_services:`` key.
        :param venues: Already-parsed workload venues for cross-reference.

        :returns: List of parsed ``WorkloadServiceSpec``.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    venues_ref = venues if venues is not None else []
    rtnval = _parse_workload_services(
        data=data, venues=venues_ref, err_lines=err_lines
    )
    _raise_if_errors(label="workload_services", err_lines=err_lines)
    return rtnval


def _parse_workload_services(*, data: Optional[list],
                             venues: List[WorkloadVenueSpec],
                             err_lines: List[str]
                             ) -> List[WorkloadServiceSpec]:
    rtnval: List[WorkloadServiceSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("workload_services must be a list.")
        return rtnval
    known_venues = {v.name for v in venues}
    for idx, entry in enumerate(raw_list):
        path = f"workload_services[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "venue", "image"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        venue_name = entry["venue"]
        if len(known_venues) > 0 and venue_name not in known_venues:
            err_lines.append(
                f"{path}.venue={venue_name!r} does not reference any "
                f"declared workload_venues[*].name."
            )
            continue
        exposure = _validate_enum(
            raw=entry.get("exposure", "ClusterIP"),
            accepted=SUPPORTED_EXPOSURES,
            path=f"{path}.exposure",
            err_lines=err_lines,
        )
        if exposure is None:
            continue
        replicas = int(entry.get("replicas", 1))
        if replicas <= 0:
            err_lines.append(
                f"{path}.replicas={replicas} must be greater than 0."
            )
            continue
        accelerators = _parse_accelerator_requests(
            raw=entry.get("accelerators"),
            path=f"{path}.accelerators",
            err_lines=err_lines,
        )
        spec = WorkloadServiceSpec(
            name=entry["name"],
            venue=venue_name,
            image=entry["image"],
            command=list(entry.get("command", [])),
            resources=dict(entry.get("resources", {})),
            accelerators=accelerators,
            replicas=replicas,
            ports=list(entry.get("ports", [])),
            env=dict(entry.get("env", {})),
            exposure=exposure,
        )
        rtnval.append(spec)
    return rtnval


# ---------------------------------------------------------------------------
# Top-level orchestrator.
# ---------------------------------------------------------------------------

def load_workload_provisioning_block(*, data: Optional[dict] = None,
                                     cloud_venues: Optional[List[CloudVenueOverrides]] = None,
                                     shared_filesystem_names: Optional[List[str]] = None,
                                     credential_lookup: Optional[CredentialLookup] = None
                                     ) -> WorkloadProvisioningBlock:
    """
        Parses and validates the full workload-provisioning portion of a
        config dict in a single pass.

        :param data: The parsed configuration dict.
        :param cloud_venues: Already-parsed cloud venues for
            ``cloud_provisioner_ref`` cross-reference.
        :param shared_filesystem_names: Names of declared shared
            filesystems used to validate ``shared_fs_mounts``.
        :param credential_lookup: Optional callable resolving
            ``credential_ref`` identifiers.

        :returns: A typed ``WorkloadProvisioningBlock``.
        :raises: ConfigurationError on validation failure.
    """
    payload = data if data is not None else {}
    venues = load_workload_venues_block(
        data=payload.get("workload_venues"),
        cloud_venues=cloud_venues,
        credential_lookup=credential_lookup,
    )
    clusters = load_workload_clusters_block(
        data=payload.get("workload_clusters"),
        venues=venues,
    )
    jobs = load_workload_jobs_block(
        data=payload.get("workload_jobs"),
        venues=venues,
        shared_filesystem_names=shared_filesystem_names,
    )
    services = load_workload_services_block(
        data=payload.get("workload_services"),
        venues=venues,
    )
    rtnval = WorkloadProvisioningBlock(
        workload_venues=venues,
        workload_clusters=clusters,
        workload_jobs=jobs,
        workload_services=services,
    )
    return rtnval


def assert_workload_kind_implemented(*, kind: str) -> None:
    """
        Raises a clear ``ConfigurationError`` when a caller asks the schema
        to act on a workload kind not implemented in v1.

        :param kind: The workload-venue kind to check.

        :raises: ConfigurationError when ``kind`` is in
            ``NOT_IMPLEMENTED_V1_KINDS``.
    """
    normalised = kind.lower() if isinstance(kind, str) else kind
    if normalised in NOT_IMPLEMENTED_V1_KINDS:
        err_lines = [
            f"Workload venue kind {kind!r} is not implemented in v1.",
            f"IMPLEMENTED KINDS: {list(IMPLEMENTED_WORKLOAD_VENUE_KINDS)!r}",
            f"DECLARABLE-BUT-NOT-IMPLEMENTED: {list(NOT_IMPLEMENTED_V1_KINDS)!r}",
        ]
        err_msg = os.linesep.join(err_lines)
        raise ConfigurationError(err_msg)
    return

"""
.. module:: test_workloadprovisioningconfigschema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Testbase tests for the workload-provisioning schema fragments.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import sys

from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parents[6]
PACKAGE_PATHS = [
    REPO_ROOT / "source" / "packages",
    REPO_ROOT / ".venv" / "src",
    REPO_ROOT / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
]
for pkg_path in PACKAGE_PATHS:
    if pkg_path.exists():
        sys.path.insert(0, str(pkg_path))


from automojo.errors.exceptions import ConfigurationError

from automojo.configuration.configurationloader import TOP_LEVEL_SCHEMA_LOADERS
from automojo.configuration.schemas.cloudprovisioningconfigschema import (
    CloudVenueOverrides,
)
from automojo.configuration.schemas.workloadprovisioningconfigschema import (
    IMPLEMENTED_WORKLOAD_VENUE_KINDS,
    NOT_IMPLEMENTED_V1_KINDS,
    WORKLOAD_VENUE_KINDS,
    WorkloadProvisioningBlock,
    WorkloadVenueSpec,
    assert_workload_kind_implemented,
    load_workload_clusters_block,
    load_workload_jobs_block,
    load_workload_provisioning_block,
    load_workload_services_block,
    load_workload_venues_block,
)


class FakeCredential:
    def __init__(self, *, identifier: str) -> None:
        self._identifier = identifier
        return


CRED_LOOKUP = (lambda identifier:
               FakeCredential(identifier=identifier)
               if identifier in {"k8s-cred", "slurm-cred"} else None)


CLOUD_VENUES = [
    CloudVenueOverrides(name="aws-primary", overrides={"region": "us-east-1"}),
]


class FakeCatalogEntry:
    def __init__(self, *, neutral_name: str) -> None:
        self.neutral_name = neutral_name
        return


class FakeAcceleratorCatalog:
    def __init__(self, *, names: List[str]) -> None:
        self._entries = [FakeCatalogEntry(neutral_name=n) for n in names]
        return

    def entries(self) -> List[FakeCatalogEntry]:
        return list(self._entries)


def _establish_venues() -> List[WorkloadVenueSpec]:
    """
        Build the standard kubernetes workload-venue fixture used as the
        per-test setUp for several of the original test classes.

        :returns: A single-element list containing the ``k8s-lab`` venue spec.
    """
    venues = [
        WorkloadVenueSpec(name="k8s-lab", kind="kubernetes",
                          credential_ref="k8s-cred"),
    ]
    return venues


def test_valid_kubernetes_venue_parses() -> None:
    data = [{"name": "k8s-lab", "kind": "KUBERNETES",
             "credential_ref": "k8s-cred"}]
    venues = load_workload_venues_block(
        data=data, credential_lookup=CRED_LOOKUP
    )
    assert len(venues) == 1
    assert venues[0].kind == "kubernetes"
    return


def test_unknown_kind_rejected() -> None:
    data = [{"name": "wv", "kind": "swarm", "credential_ref": "k8s-cred"}]
    raised = False
    try:
        load_workload_venues_block(
            data=data, credential_lookup=CRED_LOOKUP
        )
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "swarm" in msg
    assert raised
    return


def test_unresolved_credential_raises() -> None:
    data = [{"name": "k8s-lab", "kind": "kubernetes",
             "credential_ref": "no-such-cred"}]
    raised = False
    try:
        load_workload_venues_block(
            data=data, credential_lookup=CRED_LOOKUP
        )
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "no-such-cred" in msg
    assert raised
    return


def test_cloud_provisioner_ref_unknown_raises() -> None:
    data = [{"name": "k8s-lab", "kind": "kubernetes",
             "credential_ref": "k8s-cred",
             "cloud_provisioner_ref": "nope"}]
    raised = False
    try:
        load_workload_venues_block(
            data=data, cloud_venues=CLOUD_VENUES,
            credential_lookup=CRED_LOOKUP,
        )
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "nope" in msg
        assert "cloud_provisioner_ref" in msg
    assert raised
    return


def test_cloud_provisioner_ref_valid_passes() -> None:
    data = [{"name": "k8s-lab", "kind": "kubernetes",
             "credential_ref": "k8s-cred",
             "cloud_provisioner_ref": "aws-primary"}]
    venues = load_workload_venues_block(
        data=data, cloud_venues=CLOUD_VENUES,
        credential_lookup=CRED_LOOKUP,
    )
    assert venues[0].cloud_provisioner_ref == "aws-primary"
    return


def test_slurm_kind_accepted_in_yaml() -> None:
    # §7.6 — SLURM is declarable but not implemented in v1.
    data = [{"name": "slurm-lab", "kind": "slurm",
             "credential_ref": "slurm-cred"}]
    venues = load_workload_venues_block(
        data=data, credential_lookup=CRED_LOOKUP
    )
    assert venues[0].kind == "slurm"
    return


def test_missing_required_keys_raises() -> None:
    data = [{"name": "wv"}]  # no kind, no credential_ref
    raised = False
    try:
        load_workload_venues_block(data=data)
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "kind" in msg
        assert "credential_ref" in msg
    assert raised
    return


def test_cluster_unknown_venue_raises() -> None:
    venues = _establish_venues()
    data = [{"name": "c1", "venue": "nope"}]
    raised = False
    try:
        load_workload_clusters_block(data=data, venues=venues)
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "nope" in msg
    assert raised
    return


def test_cluster_with_node_pool_parses() -> None:
    venues = _establish_venues()
    data = [{"name": "c1", "venue": "k8s-lab",
             "node_pools": [
                 {"name": "cpu", "count": 3, "size": "m5.large",
                  "labels": {"pool": "cpu"}},
             ],
             "accelerator_pools": [
                 {"name": "h100", "count": 4, "size": "a3-highgpu-8g",
                  "accelerators": [
                      {"kind": "GPU", "model": "H100_SXM", "count": 8},
                  ]},
             ]}]
    clusters = load_workload_clusters_block(
        data=data, venues=venues
    )
    assert len(clusters) == 1
    assert len(clusters[0].node_pools) == 1
    assert len(clusters[0].accelerator_pools) == 1
    assert clusters[0].accelerator_pools[0].accelerators[0].model == "H100_SXM"
    return


def test_invalid_restart_policy_raises() -> None:
    venues = _establish_venues()
    data = [{"name": "j1", "venue": "k8s-lab", "image": "img",
             "restart_policy": "Always"}]
    raised = False
    try:
        load_workload_jobs_block(data=data, venues=venues)
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "Always" in msg
    assert raised
    return


def test_zero_replicas_raises() -> None:
    venues = _establish_venues()
    data = [{"name": "j1", "venue": "k8s-lab", "image": "img",
             "replicas": 0}]
    raised = False
    try:
        load_workload_jobs_block(data=data, venues=venues)
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "replicas" in msg
    assert raised
    return


def test_shared_fs_mount_unknown_fs_raises() -> None:
    venues = _establish_venues()
    data = [{"name": "j1", "venue": "k8s-lab", "image": "img",
             "shared_fs_mounts": [
                 {"filesystem_name": "ghost-fs",
                  "mount_path": "/data"},
             ]}]
    raised = False
    try:
        load_workload_jobs_block(
            data=data, venues=venues,
            shared_filesystem_names=["lab-fs"],
        )
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "ghost-fs" in msg
    assert raised
    return


def test_valid_job_parses() -> None:
    venues = _establish_venues()
    data = [{"name": "train", "venue": "k8s-lab",
             "image": "ghcr.io/lab/train:1",
             "command": ["python", "train.py"],
             "resources": {"cpu": 8, "memory": "64Gi"},
             "replicas": 1, "restart_policy": "Never",
             "env": {"WANDB_PROJECT": "lab"}}]
    jobs = load_workload_jobs_block(data=data, venues=venues)
    assert len(jobs) == 1
    assert jobs[0].restart_policy == "Never"
    return


def test_invalid_exposure_raises() -> None:
    venues = _establish_venues()
    data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
             "exposure": "PublicIngress"}]
    raised = False
    try:
        load_workload_services_block(data=data, venues=venues)
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "PublicIngress" in msg
    assert raised
    return


def test_valid_loadbalancer_service_parses() -> None:
    venues = _establish_venues()
    data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
             "exposure": "LoadBalancer",
             "ports": [{"name": "http", "containerPort": 8080,
                        "protocol": "TCP"}]}]
    services = load_workload_services_block(
        data=data, venues=venues
    )
    assert services[0].exposure == "LoadBalancer"
    return


def test_full_payload_parses() -> None:
    payload = {
        "workload_venues": [
            {"name": "k8s-lab", "kind": "kubernetes",
             "credential_ref": "k8s-cred",
             "cloud_provisioner_ref": "aws-primary"},
        ],
        "workload_clusters": [
            {"name": "c1", "venue": "k8s-lab"},
        ],
        "workload_jobs": [
            {"name": "j1", "venue": "k8s-lab", "image": "img"},
        ],
        "workload_services": [
            {"name": "s1", "venue": "k8s-lab", "image": "img"},
        ],
    }
    block = load_workload_provisioning_block(
        data=payload, cloud_venues=CLOUD_VENUES,
        credential_lookup=CRED_LOOKUP,
    )
    assert isinstance(block, WorkloadProvisioningBlock)
    assert len(block.workload_venues) == 1
    assert len(block.workload_clusters) == 1
    assert len(block.workload_jobs) == 1
    assert len(block.workload_services) == 1
    return


def test_empty_payload_yields_empty_block() -> None:
    block = load_workload_provisioning_block(data={})
    assert len(block.workload_venues) == 0
    return


def test_assert_kubernetes_does_not_raise() -> None:
    assert_workload_kind_implemented(kind="kubernetes")
    return


def test_assert_slurm_raises_with_clear_message() -> None:
    raised = False
    try:
        assert_workload_kind_implemented(kind="slurm")
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "slurm" in msg
        assert "not implemented in v1" in msg
    assert raised
    return


def test_assert_ray_raises() -> None:
    raised = False
    try:
        assert_workload_kind_implemented(kind="ray")
    except ConfigurationError:
        raised = True
    assert raised
    return


def test_assert_nomad_raises() -> None:
    raised = False
    try:
        assert_workload_kind_implemented(kind="nomad")
    except ConfigurationError:
        raised = True
    assert raised
    return


def test_kind_constants_consistent() -> None:
    for kind in IMPLEMENTED_WORKLOAD_VENUE_KINDS:
        assert kind in WORKLOAD_VENUE_KINDS
    for kind in NOT_IMPLEMENTED_V1_KINDS:
        assert kind in WORKLOAD_VENUE_KINDS
    return


def test_node_pool_accelerator_unknown_model_fails() -> None:
    venues = _establish_venues()
    catalog = FakeAcceleratorCatalog(names=["H100_SXM", "L40S"])
    data = [{"name": "c1", "venue": "k8s-lab",
             "accelerator_pools": [
                 {"name": "h100", "count": 4, "size": "a3-highgpu-8g",
                  "accelerators": [
                      {"kind": "GPU", "model": "MADE_UP_GPU",
                       "count": 8},
                  ]},
             ]}]
    raised = False
    try:
        load_workload_clusters_block(
            data=data, venues=venues,
            accelerator_catalog=catalog,
        )
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "MADE_UP_GPU" in msg
        assert "catalog" in msg
    assert raised
    return


def test_node_pool_accelerator_known_model_passes() -> None:
    venues = _establish_venues()
    catalog = FakeAcceleratorCatalog(names=["H100_SXM"])
    data = [{"name": "c1", "venue": "k8s-lab",
             "accelerator_pools": [
                 {"name": "h100", "count": 4, "size": "a3-highgpu-8g",
                  "accelerators": [
                      {"kind": "GPU", "model": "H100_SXM", "count": 8},
                  ]},
             ]}]
    clusters = load_workload_clusters_block(
        data=data, venues=venues, accelerator_catalog=catalog
    )
    assert clusters[0].accelerator_pools[0].accelerators[0].model == "H100_SXM"
    return


def test_credential_type_mismatch_fails() -> None:
    # A 'slurm' credential paired with kind 'kubernetes' is incompatible.
    kind_lookup = (lambda cred_ref:
                   "slurm" if cred_ref == "slurm-cred" else "kubernetes")
    data = [{"name": "k8s-lab", "kind": "kubernetes",
             "credential_ref": "slurm-cred"}]
    raised = False
    try:
        load_workload_venues_block(
            data=data,
            credential_lookup=CRED_LOOKUP,
            credential_kind_lookup=kind_lookup,
        )
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "slurm-cred" in msg
        assert "incompatible" in msg
    assert raised
    return


def test_credential_kind_match_passes() -> None:
    kind_lookup = (lambda cred_ref:
                   "kubernetes" if cred_ref == "k8s-cred" else "slurm")
    data = [{"name": "k8s-lab", "kind": "kubernetes",
             "credential_ref": "k8s-cred"}]
    venues = load_workload_venues_block(
        data=data,
        credential_lookup=CRED_LOOKUP,
        credential_kind_lookup=kind_lookup,
    )
    assert venues[0].kind == "kubernetes"
    return


def test_loadbalancer_exposure_rejected_when_venue_unsupported() -> None:
    venues = _establish_venues()
    no_lb_support = (lambda venue_name: False)
    data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
             "exposure": "LoadBalancer"}]
    raised = False
    try:
        load_workload_services_block(
            data=data, venues=venues,
            venue_lb_support=no_lb_support,
        )
    except ConfigurationError as ctx:
        raised = True
        msg = str(ctx)
        assert "LoadBalancer" in msg
        assert "k8s-lab" in msg
    assert raised
    return


def test_loadbalancer_exposure_accepted_when_venue_supports() -> None:
    venues = _establish_venues()
    lb_support = (lambda venue_name: True)
    data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
             "exposure": "LoadBalancer"}]
    services = load_workload_services_block(
        data=data, venues=venues, venue_lb_support=lb_support
    )
    assert services[0].exposure == "LoadBalancer"
    return


def test_clusterip_exposure_not_affected_by_lb_support() -> None:
    venues = _establish_venues()
    no_lb_support = (lambda venue_name: False)
    data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
             "exposure": "ClusterIP"}]
    services = load_workload_services_block(
        data=data, venues=venues, venue_lb_support=no_lb_support
    )
    assert services[0].exposure == "ClusterIP"
    return


def test_workload_keys_registered() -> None:
    for key in ("workload_venues", "workload_clusters",
                "workload_jobs", "workload_services"):
        assert key in TOP_LEVEL_SCHEMA_LOADERS
    return

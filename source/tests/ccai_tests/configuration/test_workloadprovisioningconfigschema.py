"""
.. module:: test_workloadprovisioningconfigschema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the workload-provisioning schema fragments.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import sys
import unittest

from pathlib import Path
from typing import List, Optional


REPO_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_PATHS = [
    REPO_ROOT / "source" / "packages",
    REPO_ROOT / ".venv" / "src",
    REPO_ROOT / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
]
for pkg_path in PACKAGE_PATHS:
    if pkg_path.exists():
        sys.path.insert(0, str(pkg_path))


from ccai.errors.exceptions import ConfigurationError

from ccai.configuration.configurationloader import TOP_LEVEL_SCHEMA_LOADERS
from ccai.configuration.schemas.cloudprovisioningconfigschema import (
    CloudVenueOverrides,
)
from ccai.configuration.schemas.workloadprovisioningconfigschema import (
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


class TestWorkloadVenuesBlock(unittest.TestCase):

    def test_valid_kubernetes_venue_parses(self):
        data = [{"name": "k8s-lab", "kind": "KUBERNETES",
                 "credential_ref": "k8s-cred"}]
        venues = load_workload_venues_block(
            data=data, credential_lookup=CRED_LOOKUP
        )
        self.assertEqual(len(venues), 1)
        self.assertEqual(venues[0].kind, "kubernetes")
        return

    def test_unknown_kind_rejected(self):
        data = [{"name": "wv", "kind": "swarm", "credential_ref": "k8s-cred"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_venues_block(
                data=data, credential_lookup=CRED_LOOKUP
            )
        msg = str(ctx.exception)
        self.assertIn("swarm", msg)
        return

    def test_unresolved_credential_raises(self):
        data = [{"name": "k8s-lab", "kind": "kubernetes",
                 "credential_ref": "no-such-cred"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_venues_block(
                data=data, credential_lookup=CRED_LOOKUP
            )
        msg = str(ctx.exception)
        self.assertIn("no-such-cred", msg)
        return

    def test_cloud_provisioner_ref_unknown_raises(self):
        data = [{"name": "k8s-lab", "kind": "kubernetes",
                 "credential_ref": "k8s-cred",
                 "cloud_provisioner_ref": "nope"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_venues_block(
                data=data, cloud_venues=CLOUD_VENUES,
                credential_lookup=CRED_LOOKUP,
            )
        msg = str(ctx.exception)
        self.assertIn("nope", msg)
        self.assertIn("cloud_provisioner_ref", msg)
        return

    def test_cloud_provisioner_ref_valid_passes(self):
        data = [{"name": "k8s-lab", "kind": "kubernetes",
                 "credential_ref": "k8s-cred",
                 "cloud_provisioner_ref": "aws-primary"}]
        venues = load_workload_venues_block(
            data=data, cloud_venues=CLOUD_VENUES,
            credential_lookup=CRED_LOOKUP,
        )
        self.assertEqual(venues[0].cloud_provisioner_ref, "aws-primary")
        return

    def test_slurm_kind_accepted_in_yaml(self):
        # §7.6 — SLURM is declarable but not implemented in v1.
        data = [{"name": "slurm-lab", "kind": "slurm",
                 "credential_ref": "slurm-cred"}]
        venues = load_workload_venues_block(
            data=data, credential_lookup=CRED_LOOKUP
        )
        self.assertEqual(venues[0].kind, "slurm")
        return

    def test_missing_required_keys_raises(self):
        data = [{"name": "wv"}]  # no kind, no credential_ref
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_venues_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("kind", msg)
        self.assertIn("credential_ref", msg)
        return


class TestWorkloadClustersBlock(unittest.TestCase):

    def setUp(self) -> None:
        self._venues = [
            WorkloadVenueSpec(name="k8s-lab", kind="kubernetes",
                              credential_ref="k8s-cred"),
        ]
        return

    def test_cluster_unknown_venue_raises(self):
        data = [{"name": "c1", "venue": "nope"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_clusters_block(data=data, venues=self._venues)
        msg = str(ctx.exception)
        self.assertIn("nope", msg)
        return

    def test_cluster_with_node_pool_parses(self):
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
            data=data, venues=self._venues
        )
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0].node_pools), 1)
        self.assertEqual(len(clusters[0].accelerator_pools), 1)
        self.assertEqual(
            clusters[0].accelerator_pools[0].accelerators[0].model,
            "H100_SXM",
        )
        return


class TestWorkloadJobsBlock(unittest.TestCase):

    def setUp(self) -> None:
        self._venues = [
            WorkloadVenueSpec(name="k8s-lab", kind="kubernetes",
                              credential_ref="k8s-cred"),
        ]
        return

    def test_invalid_restart_policy_raises(self):
        data = [{"name": "j1", "venue": "k8s-lab", "image": "img",
                 "restart_policy": "Always"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_jobs_block(data=data, venues=self._venues)
        msg = str(ctx.exception)
        self.assertIn("Always", msg)
        return

    def test_zero_replicas_raises(self):
        data = [{"name": "j1", "venue": "k8s-lab", "image": "img",
                 "replicas": 0}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_jobs_block(data=data, venues=self._venues)
        msg = str(ctx.exception)
        self.assertIn("replicas", msg)
        return

    def test_shared_fs_mount_unknown_fs_raises(self):
        data = [{"name": "j1", "venue": "k8s-lab", "image": "img",
                 "shared_fs_mounts": [
                     {"filesystem_name": "ghost-fs",
                      "mount_path": "/data"},
                 ]}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_jobs_block(
                data=data, venues=self._venues,
                shared_filesystem_names=["lab-fs"],
            )
        msg = str(ctx.exception)
        self.assertIn("ghost-fs", msg)
        return

    def test_valid_job_parses(self):
        data = [{"name": "train", "venue": "k8s-lab",
                 "image": "ghcr.io/lab/train:1",
                 "command": ["python", "train.py"],
                 "resources": {"cpu": 8, "memory": "64Gi"},
                 "replicas": 1, "restart_policy": "Never",
                 "env": {"WANDB_PROJECT": "lab"}}]
        jobs = load_workload_jobs_block(data=data, venues=self._venues)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].restart_policy, "Never")
        return


class TestWorkloadServicesBlock(unittest.TestCase):

    def setUp(self) -> None:
        self._venues = [
            WorkloadVenueSpec(name="k8s-lab", kind="kubernetes",
                              credential_ref="k8s-cred"),
        ]
        return

    def test_invalid_exposure_raises(self):
        data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
                 "exposure": "PublicIngress"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_services_block(data=data, venues=self._venues)
        msg = str(ctx.exception)
        self.assertIn("PublicIngress", msg)
        return

    def test_valid_loadbalancer_service_parses(self):
        data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
                 "exposure": "LoadBalancer",
                 "ports": [{"name": "http", "containerPort": 8080,
                            "protocol": "TCP"}]}]
        services = load_workload_services_block(
            data=data, venues=self._venues
        )
        self.assertEqual(services[0].exposure, "LoadBalancer")
        return


class TestFullWorkloadBlock(unittest.TestCase):

    def test_full_payload_parses(self):
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
        self.assertIsInstance(block, WorkloadProvisioningBlock)
        self.assertEqual(len(block.workload_venues), 1)
        self.assertEqual(len(block.workload_clusters), 1)
        self.assertEqual(len(block.workload_jobs), 1)
        self.assertEqual(len(block.workload_services), 1)
        return

    def test_empty_payload_yields_empty_block(self):
        block = load_workload_provisioning_block(data={})
        self.assertEqual(len(block.workload_venues), 0)
        return


class TestKindImplementationGuard(unittest.TestCase):

    def test_assert_kubernetes_does_not_raise(self):
        assert_workload_kind_implemented(kind="kubernetes")
        return

    def test_assert_slurm_raises_with_clear_message(self):
        with self.assertRaises(ConfigurationError) as ctx:
            assert_workload_kind_implemented(kind="slurm")
        msg = str(ctx.exception)
        self.assertIn("slurm", msg)
        self.assertIn("not implemented in v1", msg)
        return

    def test_assert_ray_raises(self):
        with self.assertRaises(ConfigurationError):
            assert_workload_kind_implemented(kind="ray")
        return

    def test_assert_nomad_raises(self):
        with self.assertRaises(ConfigurationError):
            assert_workload_kind_implemented(kind="nomad")
        return

    def test_kind_constants_consistent(self):
        for kind in IMPLEMENTED_WORKLOAD_VENUE_KINDS:
            self.assertIn(kind, WORKLOAD_VENUE_KINDS)
        for kind in NOT_IMPLEMENTED_V1_KINDS:
            self.assertIn(kind, WORKLOAD_VENUE_KINDS)
        return


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


class TestNodePoolAcceleratorCatalog(unittest.TestCase):

    def setUp(self) -> None:
        self._venues = [
            WorkloadVenueSpec(name="k8s-lab", kind="kubernetes",
                              credential_ref="k8s-cred"),
        ]
        return

    def test_node_pool_accelerator_unknown_model_fails(self):
        catalog = FakeAcceleratorCatalog(names=["H100_SXM", "L40S"])
        data = [{"name": "c1", "venue": "k8s-lab",
                 "accelerator_pools": [
                     {"name": "h100", "count": 4, "size": "a3-highgpu-8g",
                      "accelerators": [
                          {"kind": "GPU", "model": "MADE_UP_GPU",
                           "count": 8},
                      ]},
                 ]}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_clusters_block(
                data=data, venues=self._venues,
                accelerator_catalog=catalog,
            )
        msg = str(ctx.exception)
        self.assertIn("MADE_UP_GPU", msg)
        self.assertIn("catalog", msg)
        return

    def test_node_pool_accelerator_known_model_passes(self):
        catalog = FakeAcceleratorCatalog(names=["H100_SXM"])
        data = [{"name": "c1", "venue": "k8s-lab",
                 "accelerator_pools": [
                     {"name": "h100", "count": 4, "size": "a3-highgpu-8g",
                      "accelerators": [
                          {"kind": "GPU", "model": "H100_SXM", "count": 8},
                      ]},
                 ]}]
        clusters = load_workload_clusters_block(
            data=data, venues=self._venues, accelerator_catalog=catalog
        )
        self.assertEqual(
            clusters[0].accelerator_pools[0].accelerators[0].model,
            "H100_SXM",
        )
        return


class TestCredentialKindCompatibility(unittest.TestCase):

    def test_credential_type_mismatch_fails(self):
        # A 'slurm' credential paired with kind 'kubernetes' is incompatible.
        kind_lookup = (lambda cred_ref:
                       "slurm" if cred_ref == "slurm-cred" else "kubernetes")
        data = [{"name": "k8s-lab", "kind": "kubernetes",
                 "credential_ref": "slurm-cred"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_venues_block(
                data=data,
                credential_lookup=CRED_LOOKUP,
                credential_kind_lookup=kind_lookup,
            )
        msg = str(ctx.exception)
        self.assertIn("slurm-cred", msg)
        self.assertIn("incompatible", msg)
        return

    def test_credential_kind_match_passes(self):
        kind_lookup = (lambda cred_ref:
                       "kubernetes" if cred_ref == "k8s-cred" else "slurm")
        data = [{"name": "k8s-lab", "kind": "kubernetes",
                 "credential_ref": "k8s-cred"}]
        venues = load_workload_venues_block(
            data=data,
            credential_lookup=CRED_LOOKUP,
            credential_kind_lookup=kind_lookup,
        )
        self.assertEqual(venues[0].kind, "kubernetes")
        return


class TestLoadBalancerVenueSupport(unittest.TestCase):

    def setUp(self) -> None:
        self._venues = [
            WorkloadVenueSpec(name="k8s-lab", kind="kubernetes",
                              credential_ref="k8s-cred"),
        ]
        return

    def test_loadbalancer_exposure_rejected_when_venue_unsupported(self):
        no_lb_support = (lambda venue_name: False)
        data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
                 "exposure": "LoadBalancer"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_workload_services_block(
                data=data, venues=self._venues,
                venue_lb_support=no_lb_support,
            )
        msg = str(ctx.exception)
        self.assertIn("LoadBalancer", msg)
        self.assertIn("k8s-lab", msg)
        return

    def test_loadbalancer_exposure_accepted_when_venue_supports(self):
        lb_support = (lambda venue_name: True)
        data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
                 "exposure": "LoadBalancer"}]
        services = load_workload_services_block(
            data=data, venues=self._venues, venue_lb_support=lb_support
        )
        self.assertEqual(services[0].exposure, "LoadBalancer")
        return

    def test_clusterip_exposure_not_affected_by_lb_support(self):
        no_lb_support = (lambda venue_name: False)
        data = [{"name": "s1", "venue": "k8s-lab", "image": "img",
                 "exposure": "ClusterIP"}]
        services = load_workload_services_block(
            data=data, venues=self._venues, venue_lb_support=no_lb_support
        )
        self.assertEqual(services[0].exposure, "ClusterIP")
        return


class TestTopLevelRegistry(unittest.TestCase):

    def test_workload_keys_registered(self):
        for key in ("workload_venues", "workload_clusters",
                    "workload_jobs", "workload_services"):
            self.assertIn(key, TOP_LEVEL_SCHEMA_LOADERS)
        return


if __name__ == "__main__":
    unittest.main()

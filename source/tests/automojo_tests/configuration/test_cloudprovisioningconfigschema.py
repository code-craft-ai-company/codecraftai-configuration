"""
.. module:: test_cloudprovisioningconfigschema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the cloud-provisioning schema fragments.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
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


from automojo.errors.exceptions import ConfigurationError

from automojo.configuration.configurationloader import TOP_LEVEL_SCHEMA_LOADERS
from automojo.configuration.schemas.vpnconfigschema import (
    AddressPlane,
    VPNBlock,
    VPNOverlayProfile,
)
from automojo.configuration.schemas.cloudprovisioningconfigschema import (
    CloudAcceleratorAssignment,
    CloudInstanceSpec,
    CloudNetworkSpec,
    CloudProvisioningBlock,
    CloudSharedFilesystem,
    CloudSubnetSpec,
    VPNJoinSpec,
    dump_cloud_networks_block,
    dump_cloud_subnets_block,
    load_cloud_accelerators_block,
    load_cloud_buckets_block,
    load_cloud_dns_records_block,
    load_cloud_images_block,
    load_cloud_instances_block,
    load_cloud_keypairs_block,
    load_cloud_load_balancers_block,
    load_cloud_networks_block,
    load_cloud_provisioning_block,
    load_cloud_security_groups_block,
    load_cloud_shared_filesystems_block,
    load_cloud_subnets_block,
    load_cloud_venues_block,
    load_cloud_volumes_block,
)


class FakeCredential:
    def __init__(self, *, identifier: str, categories: List[str]) -> None:
        self._identifier = identifier
        self._categories = categories
        return

    @property
    def categories(self) -> List[str]:
        return self._categories


def make_credential_lookup(creds: dict):
    def _lookup(identifier: str) -> Optional[FakeCredential]:
        rtnval = creds.get(identifier)
        return rtnval
    return _lookup


VPN_BLOCK = VPNBlock(
    default_plane=AddressPlane.OVERLAY,
    providers=[
        VPNOverlayProfile(
            name="lab-tailnet",
            provider="tailscale",
            network="acme.ts.net",
        ),
    ],
)


CRED_LOOKUP = make_credential_lookup({
    "ts-prov-oauth": FakeCredential(
        identifier="ts-prov-oauth",
        categories=["tailscale-oauth"],
    ),
})


def make_full_payload() -> dict:
    rtnval = {
        "networks": [
            {"name": "lab-vpc", "cidr": "10.0.0.0/16", "region": "us-east-1",
             "tags": [{"env": "ci"}]},
        ],
        "subnets": [
            {"name": "lab-subnet-a", "network": "lab-vpc",
             "cidr": "10.0.1.0/24", "zone": "us-east-1a", "public": True},
        ],
        "security_groups": [
            {"name": "lab-web", "network": "lab-vpc",
             "ingress_rules": [
                 {"protocol": "tcp", "from_port": 22, "to_port": 22,
                  "source_cidrs": ["0.0.0.0/0"], "description": "ssh"},
             ]},
        ],
        "keypairs": [
            {"name": "lab-key", "public_key": "ssh-ed25519 AAAA..."},
        ],
        "images": [
            {"name": "ubuntu-24", "family": "ubuntu", "version": "24.04",
             "architecture": "x86_64"},
        ],
        "instances": [
            {"name": "web-01", "image": "ubuntu-24", "size": "small",
             "subnet": "lab-subnet-a", "security_groups": ["lab-web"],
             "keypair": "lab-key", "public_ip": True,
             "vpn_join": {
                 "provider": "lab-tailnet",
                 "control_plane_credential": "ts-prov-oauth",
                 "advertise_tags": ["tag:lab"],
                 "hostname_template": "{name}-lab",
             }},
        ],
        "volumes": [
            {"name": "data-vol", "kind": "block", "size_gb": 100,
             "zone": "us-east-1a"},
        ],
        "buckets": [
            {"name": "lab-bucket", "region": "us-east-1", "versioning": True},
        ],
        "load_balancers": [
            {"name": "web-lb", "scheme": "internet-facing",
             "subnet": "lab-subnet-a", "targets": ["web-01"]},
        ],
        "dns_records": [
            {"name": "web.lab.example.com", "record_type": "A",
             "values": ["192.0.2.1"], "ttl": 60},
        ],
        "venues": {
            "aws-primary": {"profile": "lab", "extra": True},
        },
    }
    return rtnval


class TestCloudProvisioningBlock(unittest.TestCase):

    def test_full_payload_parses(self):
        payload = make_full_payload()
        block = load_cloud_provisioning_block(
            data=payload, vpn_block=VPN_BLOCK, credential_lookup=CRED_LOOKUP
        )
        self.assertIsInstance(block, CloudProvisioningBlock)
        self.assertEqual(len(block.networks), 1)
        self.assertEqual(len(block.subnets), 1)
        self.assertEqual(len(block.security_groups), 1)
        self.assertEqual(len(block.keypairs), 1)
        self.assertEqual(len(block.images), 1)
        self.assertEqual(len(block.instances), 1)
        self.assertEqual(len(block.volumes), 1)
        self.assertEqual(len(block.buckets), 1)
        self.assertEqual(len(block.load_balancers), 1)
        self.assertEqual(len(block.dns_records), 1)
        self.assertEqual(len(block.venues), 1)
        return

    def test_empty_payload_yields_empty_block(self):
        block = load_cloud_provisioning_block(data={})
        self.assertEqual(len(block.networks), 0)
        self.assertEqual(len(block.instances), 0)
        return

    def test_none_payload_yields_empty_block(self):
        block = load_cloud_provisioning_block(data=None)
        self.assertEqual(len(block.networks), 0)
        return


class TestNetworksBlock(unittest.TestCase):

    def test_missing_required_field_raises(self):
        data = [{"name": "n1", "region": "us-east-1"}]  # no cidr
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_networks_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("cidr", msg)
        self.assertIn("networks[0]", msg)
        return

    def test_bad_cidr_raises(self):
        data = [{"name": "n1", "cidr": "not-a-cidr", "region": "us-east-1"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_networks_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("not-a-cidr", msg)
        self.assertIn("cidr", msg)
        return

    def test_dump_round_trip(self):
        data = [
            {"name": "lab-vpc", "cidr": "10.0.0.0/16",
             "region": "us-east-1", "tags": [{"env": "ci"}]},
        ]
        networks = load_cloud_networks_block(data=data)
        dumped = dump_cloud_networks_block(networks=networks)
        self.assertEqual(dumped, data)
        return


class TestSubnetsBlock(unittest.TestCase):

    def setUp(self) -> None:
        self._networks = [
            CloudNetworkSpec(name="lab-vpc", cidr="10.0.0.0/16",
                             region="us-east-1"),
        ]
        return

    def test_subnet_unknown_network_raises_with_both_sides(self):
        data = [{"name": "sub-a", "network": "missing-vpc",
                 "cidr": "10.0.1.0/24", "zone": "us-east-1a"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_subnets_block(data=data, networks=self._networks)
        msg = str(ctx.exception)
        self.assertIn("missing-vpc", msg)
        self.assertIn("subnets[0].network", msg)
        return

    def test_subnet_bad_cidr_raises(self):
        data = [{"name": "sub-a", "network": "lab-vpc",
                 "cidr": "999.999.999.0/24", "zone": "us-east-1a"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_subnets_block(data=data, networks=self._networks)
        msg = str(ctx.exception)
        self.assertIn("999.999", msg)
        return

    def test_subnet_dump_round_trip(self):
        data = [{"name": "sub-a", "network": "lab-vpc",
                 "cidr": "10.0.1.0/24", "zone": "us-east-1a", "public": True}]
        subnets = load_cloud_subnets_block(
            data=data, networks=self._networks
        )
        dumped = dump_cloud_subnets_block(subnets=subnets)
        self.assertEqual(dumped, data)
        return


class TestSecurityGroupsBlock(unittest.TestCase):

    def setUp(self) -> None:
        self._networks = [
            CloudNetworkSpec(name="lab-vpc", cidr="10.0.0.0/16",
                             region="us-east-1"),
        ]
        return

    def test_unknown_protocol_rejected(self):
        data = [{"name": "sg1", "network": "lab-vpc",
                 "ingress_rules": [{"protocol": "smtp", "from_port": 25,
                                    "to_port": 25}]}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_security_groups_block(
                data=data, networks=self._networks
            )
        msg = str(ctx.exception)
        self.assertIn("smtp", msg)
        return

    def test_sg_unknown_network_raises(self):
        data = [{"name": "sg1", "network": "nope"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_security_groups_block(
                data=data, networks=self._networks
            )
        msg = str(ctx.exception)
        self.assertIn("nope", msg)
        return


class TestInstancesBlock(unittest.TestCase):

    def setUp(self) -> None:
        self._networks = [
            CloudNetworkSpec(name="lab-vpc", cidr="10.0.0.0/16",
                             region="us-east-1"),
        ]
        self._subnets = [
            CloudSubnetSpec(name="sub-a", network="lab-vpc",
                            cidr="10.0.1.0/24", zone="us-east-1a"),
        ]
        self._security_groups = load_cloud_security_groups_block(
            data=[{"name": "sg-web", "network": "lab-vpc"}],
            networks=self._networks,
        )
        self._keypairs = load_cloud_keypairs_block(
            data=[{"name": "kp", "public_key": "ssh-ed25519 AAA"}]
        )
        self._images = load_cloud_images_block(
            data=[{"name": "ubuntu-24", "family": "ubuntu",
                   "version": "24.04"}]
        )
        return

    def test_instance_unknown_image_raises(self):
        data = [{"name": "i1", "image": "nope", "size": "small",
                 "subnet": "sub-a"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_instances_block(
                data=data,
                images=self._images,
                subnets=self._subnets,
                security_groups=self._security_groups,
                keypairs=self._keypairs,
            )
        msg = str(ctx.exception)
        self.assertIn("nope", msg)
        self.assertIn("image", msg)
        return

    def test_instance_unknown_subnet_raises(self):
        data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
                 "subnet": "missing"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_instances_block(
                data=data,
                images=self._images,
                subnets=self._subnets,
                security_groups=self._security_groups,
                keypairs=self._keypairs,
            )
        msg = str(ctx.exception)
        self.assertIn("missing", msg)
        return

    def test_instance_unknown_security_group_raises(self):
        data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
                 "subnet": "sub-a", "security_groups": ["bogus"]}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_instances_block(
                data=data,
                images=self._images,
                subnets=self._subnets,
                security_groups=self._security_groups,
                keypairs=self._keypairs,
            )
        msg = str(ctx.exception)
        self.assertIn("bogus", msg)
        return

    def test_instance_unknown_keypair_raises(self):
        data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
                 "subnet": "sub-a", "keypair": "no-kp"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_instances_block(
                data=data,
                images=self._images,
                subnets=self._subnets,
                security_groups=self._security_groups,
                keypairs=self._keypairs,
            )
        msg = str(ctx.exception)
        self.assertIn("no-kp", msg)
        return

    def test_instance_vpn_join_unknown_provider_raises(self):
        data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
                 "subnet": "sub-a",
                 "vpn_join": {"provider": "no-provider",
                              "control_plane_credential": "ts-prov-oauth",
                              "hostname_template": "{name}-lab"}}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_instances_block(
                data=data,
                images=self._images,
                subnets=self._subnets,
                security_groups=self._security_groups,
                keypairs=self._keypairs,
                vpn_block=VPN_BLOCK,
                credential_lookup=CRED_LOOKUP,
            )
        msg = str(ctx.exception)
        self.assertIn("no-provider", msg)
        self.assertIn("vpn.providers", msg)
        return

    def test_instance_vpn_join_unresolved_credential_raises(self):
        data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
                 "subnet": "sub-a",
                 "vpn_join": {"provider": "lab-tailnet",
                              "control_plane_credential": "no-such",
                              "hostname_template": "{name}-lab"}}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_instances_block(
                data=data,
                images=self._images,
                subnets=self._subnets,
                security_groups=self._security_groups,
                keypairs=self._keypairs,
                vpn_block=VPN_BLOCK,
                credential_lookup=CRED_LOOKUP,
            )
        msg = str(ctx.exception)
        self.assertIn("no-such", msg)
        return

    def test_instance_with_valid_vpn_join_parses(self):
        data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
                 "subnet": "sub-a",
                 "vpn_join": {"provider": "lab-tailnet",
                              "control_plane_credential": "ts-prov-oauth",
                              "advertise_tags": ["tag:lab"],
                              "hostname_template": "{name}-lab"}}]
        instances = load_cloud_instances_block(
            data=data,
            images=self._images,
            subnets=self._subnets,
            security_groups=self._security_groups,
            keypairs=self._keypairs,
            vpn_block=VPN_BLOCK,
            credential_lookup=CRED_LOOKUP,
        )
        self.assertEqual(len(instances), 1)
        self.assertIsInstance(instances[0], CloudInstanceSpec)
        self.assertIsInstance(instances[0].vpn_join, VPNJoinSpec)
        self.assertEqual(
            instances[0].vpn_join.control_plane_credential, "ts-prov-oauth"
        )
        return


class TestVolumesBlock(unittest.TestCase):

    def test_volume_without_size_or_existing_raises(self):
        data = [{"name": "vol1", "kind": "block"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_volumes_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("size_gb", msg)
        self.assertIn("existing_id", msg)
        return

    def test_volume_unknown_kind_rejected(self):
        data = [{"name": "vol1", "kind": "magnetic", "size_gb": 10}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_volumes_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("magnetic", msg)
        return


class TestDnsRecordsBlock(unittest.TestCase):

    def test_unknown_record_type_rejected(self):
        data = [{"name": "x", "record_type": "QQQ", "values": ["1.2.3.4"]}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_dns_records_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("QQQ", msg)
        return

    def test_empty_values_rejected(self):
        data = [{"name": "x", "record_type": "A", "values": []}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_dns_records_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("values", msg)
        return


class TestLoadBalancersBlock(unittest.TestCase):

    def test_lb_unknown_target_raises(self):
        subnets = [CloudSubnetSpec(name="sub-a", network="lab-vpc",
                                   cidr="10.0.1.0/24", zone="us-east-1a")]
        data = [{"name": "lb1", "scheme": "internet-facing",
                 "subnet": "sub-a", "targets": ["ghost"]}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_load_balancers_block(
                data=data, subnets=subnets, instances=[]
            )
        msg = str(ctx.exception)
        self.assertIn("ghost", msg)
        return


class TestVenuesBlock(unittest.TestCase):

    def test_venues_forwarded_verbatim(self):
        data = {"aws-primary": {"some_key": 1, "nested": {"x": "y"}}}
        venues = load_cloud_venues_block(data=data)
        self.assertEqual(len(venues), 1)
        self.assertEqual(venues[0].name, "aws-primary")
        self.assertEqual(venues[0].overrides, {"some_key": 1,
                                               "nested": {"x": "y"}})
        return


class TestBucketsBlock(unittest.TestCase):

    def test_missing_region_raises(self):
        data = [{"name": "b1"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_buckets_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("region", msg)
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


class TestAcceleratorsBlock(unittest.TestCase):

    def setUp(self) -> None:
        self._instances = [
            CloudInstanceSpec(name="trainer-01", image="ubuntu-24",
                              size="large", subnet="sub-a"),
        ]
        return

    def test_accelerator_references_unknown_instance_fails(self):
        data = [
            {"instance_name": "ghost-instance",
             "accelerators": [
                 {"kind": "GPU", "model": "H100_SXM", "count": 8,
                  "memory_gb": 80},
             ]},
        ]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_accelerators_block(
                data=data, instances=self._instances
            )
        msg = str(ctx.exception)
        self.assertIn("ghost-instance", msg)
        self.assertIn("instance_name", msg)
        self.assertIn("devices[*].name", msg)
        return

    def test_accelerator_valid_reference_parses(self):
        data = [
            {"instance_name": "trainer-01",
             "accelerators": [
                 {"kind": "GPU", "model": "H100_SXM", "count": 8,
                  "interconnect": "NVSWITCH", "memory_gb": 80},
             ]},
        ]
        assignments = load_cloud_accelerators_block(
            data=data, instances=self._instances
        )
        self.assertEqual(len(assignments), 1)
        self.assertIsInstance(assignments[0], CloudAcceleratorAssignment)
        self.assertEqual(assignments[0].instance_name, "trainer-01")
        self.assertEqual(assignments[0].accelerators[0].model, "H100_SXM")
        return

    def test_accelerator_unknown_catalog_model_fails(self):
        catalog = FakeAcceleratorCatalog(names=["H100_SXM"])
        data = [
            {"instance_name": "trainer-01",
             "accelerators": [
                 {"kind": "GPU", "model": "MADE_UP_GPU", "count": 1,
                  "memory_gb": 40},
             ]},
        ]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_accelerators_block(
                data=data, instances=self._instances,
                accelerator_catalog=catalog,
            )
        msg = str(ctx.exception)
        self.assertIn("MADE_UP_GPU", msg)
        self.assertIn("catalog", msg)
        return


class TestSharedFilesystemsBlock(unittest.TestCase):

    def test_shared_fs_attach_or_provision_discriminator(self):
        # Neither size_tb nor existing_id present -- must fail.
        data = [{"name": "scratch-fs", "kind": "LUSTRE"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_shared_filesystems_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("size_tb", msg)
        self.assertIn("existing_id", msg)
        return

    def test_shared_fs_provision_mode_parses(self):
        data = [{"name": "scratch-fs", "kind": "LUSTRE", "size_tb": 10}]
        filesystems = load_cloud_shared_filesystems_block(data=data)
        self.assertEqual(len(filesystems), 1)
        self.assertIsInstance(filesystems[0], CloudSharedFilesystem)
        self.assertEqual(filesystems[0].size_tb, 10)
        return

    def test_shared_fs_attach_mode_parses(self):
        data = [{"name": "scratch-fs", "kind": "EFS",
                 "existing_id": "fs-0abc123"}]
        filesystems = load_cloud_shared_filesystems_block(data=data)
        self.assertEqual(len(filesystems), 1)
        self.assertEqual(filesystems[0].existing_id, "fs-0abc123")
        return

    def test_shared_fs_unknown_kind_rejected(self):
        data = [{"name": "scratch-fs", "kind": "NOTAFS", "size_tb": 1}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_shared_filesystems_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("NOTAFS", msg)
        return


class TestGuardedIntConversions(unittest.TestCase):
    """
        Regression tests for the audit MEDIUM finding that unguarded
        ``int(...)`` conversions could let a ``ValueError`` / ``TypeError``
        escape as an uncaught crash instead of an accumulated
        ``ConfigurationError``.
    """

    def test_dns_record_non_numeric_ttl_raises_configuration_error(self):
        data = [{"name": "web.example.com", "record_type": "A",
                 "values": ["192.0.2.1"], "ttl": "not-a-number"}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_dns_records_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("ttl", msg)
        return

    def test_accelerator_requires_memory_gb(self):
        data = [{"instance_name": "i1",
                 "accelerators": [{"kind": "GPU", "model": "H100_SXM",
                                   "count": 8}]}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_accelerators_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("memory_gb", msg)
        return

    def test_accelerator_non_numeric_count_raises(self):
        data = [{"instance_name": "i1",
                 "accelerators": [{"kind": "GPU", "model": "H100_SXM",
                                   "count": "many", "memory_gb": 80}]}]
        with self.assertRaises(ConfigurationError) as ctx:
            load_cloud_accelerators_block(data=data)
        msg = str(ctx.exception)
        self.assertIn("count", msg)
        return


class TestTopLevelRegistry(unittest.TestCase):

    def test_cloud_keys_registered(self):
        expected = (
            "networks", "subnets", "security_groups", "keypairs", "images",
            "instances", "volumes", "buckets", "load_balancers", "dns_records",
            "accelerators", "shared_filesystems",
        )
        for key in expected:
            self.assertIn(key, TOP_LEVEL_SCHEMA_LOADERS)
        return


if __name__ == "__main__":
    unittest.main()

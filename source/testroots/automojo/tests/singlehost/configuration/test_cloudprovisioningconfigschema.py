"""
.. module:: test_cloudprovisioningconfigschema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Testbase tests for the cloud-provisioning schema fragments.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import sys

from pathlib import Path
from typing import Callable, List, Optional


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


def make_credential_lookup(creds: dict) -> Callable[[str], Optional["FakeCredential"]]:
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


def _establish_subnet_networks() -> List[CloudNetworkSpec]:
    """
        Establish the per-test network fixture used by the subnets-block tests
        (replicates the original ``TestSubnetsBlock.setUp``).

        :returns: A single-element list holding the ``lab-vpc`` network spec.
    """
    networks = [
        CloudNetworkSpec(name="lab-vpc", cidr="10.0.0.0/16",
                         region="us-east-1"),
    ]
    return networks


def _establish_security_group_networks() -> List[CloudNetworkSpec]:
    """
        Establish the per-test network fixture used by the security-groups
        block tests (replicates the original
        ``TestSecurityGroupsBlock.setUp``).

        :returns: A single-element list holding the ``lab-vpc`` network spec.
    """
    networks = [
        CloudNetworkSpec(name="lab-vpc", cidr="10.0.0.0/16",
                         region="us-east-1"),
    ]
    return networks


def _establish_instance_env() -> dict:
    """
        Establish the per-test instances fixture (replicates the original
        ``TestInstancesBlock.setUp``).

        :returns: A dictionary of the network, subnet, security-group,
                  keypair, and image fixtures keyed by name.
    """
    networks = [
        CloudNetworkSpec(name="lab-vpc", cidr="10.0.0.0/16",
                         region="us-east-1"),
    ]
    subnets = [
        CloudSubnetSpec(name="sub-a", network="lab-vpc",
                        cidr="10.0.1.0/24", zone="us-east-1a"),
    ]
    security_groups = load_cloud_security_groups_block(
        data=[{"name": "sg-web", "network": "lab-vpc"}],
        networks=networks,
    )
    keypairs = load_cloud_keypairs_block(
        data=[{"name": "kp", "public_key": "ssh-ed25519 AAA"}]
    )
    images = load_cloud_images_block(
        data=[{"name": "ubuntu-24", "family": "ubuntu",
               "version": "24.04"}]
    )
    env = {
        "networks": networks,
        "subnets": subnets,
        "security_groups": security_groups,
        "keypairs": keypairs,
        "images": images,
    }
    return env


def _establish_accelerator_instances() -> List[CloudInstanceSpec]:
    """
        Establish the per-test instances fixture used by the accelerators
        block tests (replicates the original ``TestAcceleratorsBlock.setUp``).

        :returns: A single-element list holding the ``trainer-01`` instance
                  spec.
    """
    instances = [
        CloudInstanceSpec(name="trainer-01", image="ubuntu-24",
                          size="large", subnet="sub-a"),
    ]
    return instances


def test_full_payload_parses() -> None:
    payload = make_full_payload()
    block = load_cloud_provisioning_block(
        data=payload, vpn_block=VPN_BLOCK, credential_lookup=CRED_LOOKUP
    )
    assert isinstance(block, CloudProvisioningBlock)
    assert len(block.networks) == 1
    assert len(block.subnets) == 1
    assert len(block.security_groups) == 1
    assert len(block.keypairs) == 1
    assert len(block.images) == 1
    assert len(block.instances) == 1
    assert len(block.volumes) == 1
    assert len(block.buckets) == 1
    assert len(block.load_balancers) == 1
    assert len(block.dns_records) == 1
    assert len(block.venues) == 1
    return


def test_empty_payload_yields_empty_block() -> None:
    block = load_cloud_provisioning_block(data={})
    assert len(block.networks) == 0
    assert len(block.instances) == 0
    return


def test_none_payload_yields_empty_block() -> None:
    block = load_cloud_provisioning_block(data=None)
    assert len(block.networks) == 0
    return


def test_missing_required_field_raises() -> None:
    data = [{"name": "n1", "region": "us-east-1"}]  # no cidr
    raised = False
    try:
        load_cloud_networks_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "cidr" in msg
        assert "networks[0]" in msg
    assert raised
    return


def test_bad_cidr_raises() -> None:
    data = [{"name": "n1", "cidr": "not-a-cidr", "region": "us-east-1"}]
    raised = False
    try:
        load_cloud_networks_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "not-a-cidr" in msg
        assert "cidr" in msg
    assert raised
    return


def test_dump_round_trip() -> None:
    data = [
        {"name": "lab-vpc", "cidr": "10.0.0.0/16",
         "region": "us-east-1", "tags": [{"env": "ci"}]},
    ]
    networks = load_cloud_networks_block(data=data)
    dumped = dump_cloud_networks_block(networks=networks)
    assert dumped == data
    return


def test_subnet_unknown_network_raises_with_both_sides() -> None:
    networks = _establish_subnet_networks()
    data = [{"name": "sub-a", "network": "missing-vpc",
             "cidr": "10.0.1.0/24", "zone": "us-east-1a"}]
    raised = False
    try:
        load_cloud_subnets_block(data=data, networks=networks)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "missing-vpc" in msg
        assert "subnets[0].network" in msg
    assert raised
    return


def test_subnet_bad_cidr_raises() -> None:
    networks = _establish_subnet_networks()
    data = [{"name": "sub-a", "network": "lab-vpc",
             "cidr": "999.999.999.0/24", "zone": "us-east-1a"}]
    raised = False
    try:
        load_cloud_subnets_block(data=data, networks=networks)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "999.999" in msg
    assert raised
    return


def test_subnet_dump_round_trip() -> None:
    networks = _establish_subnet_networks()
    data = [{"name": "sub-a", "network": "lab-vpc",
             "cidr": "10.0.1.0/24", "zone": "us-east-1a", "public": True}]
    subnets = load_cloud_subnets_block(
        data=data, networks=networks
    )
    dumped = dump_cloud_subnets_block(subnets=subnets)
    assert dumped == data
    return


def test_unknown_protocol_rejected() -> None:
    networks = _establish_security_group_networks()
    data = [{"name": "sg1", "network": "lab-vpc",
             "ingress_rules": [{"protocol": "smtp", "from_port": 25,
                                "to_port": 25}]}]
    raised = False
    try:
        load_cloud_security_groups_block(
            data=data, networks=networks
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "smtp" in msg
    assert raised
    return


def test_sg_unknown_network_raises() -> None:
    networks = _establish_security_group_networks()
    data = [{"name": "sg1", "network": "nope"}]
    raised = False
    try:
        load_cloud_security_groups_block(
            data=data, networks=networks
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "nope" in msg
    assert raised
    return


def test_instance_unknown_image_raises() -> None:
    env = _establish_instance_env()
    data = [{"name": "i1", "image": "nope", "size": "small",
             "subnet": "sub-a"}]
    raised = False
    try:
        load_cloud_instances_block(
            data=data,
            images=env["images"],
            subnets=env["subnets"],
            security_groups=env["security_groups"],
            keypairs=env["keypairs"],
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "nope" in msg
        assert "image" in msg
    assert raised
    return


def test_instance_unknown_subnet_raises() -> None:
    env = _establish_instance_env()
    data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
             "subnet": "missing"}]
    raised = False
    try:
        load_cloud_instances_block(
            data=data,
            images=env["images"],
            subnets=env["subnets"],
            security_groups=env["security_groups"],
            keypairs=env["keypairs"],
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "missing" in msg
    assert raised
    return


def test_instance_unknown_security_group_raises() -> None:
    env = _establish_instance_env()
    data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
             "subnet": "sub-a", "security_groups": ["bogus"]}]
    raised = False
    try:
        load_cloud_instances_block(
            data=data,
            images=env["images"],
            subnets=env["subnets"],
            security_groups=env["security_groups"],
            keypairs=env["keypairs"],
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "bogus" in msg
    assert raised
    return


def test_instance_unknown_keypair_raises() -> None:
    env = _establish_instance_env()
    data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
             "subnet": "sub-a", "keypair": "no-kp"}]
    raised = False
    try:
        load_cloud_instances_block(
            data=data,
            images=env["images"],
            subnets=env["subnets"],
            security_groups=env["security_groups"],
            keypairs=env["keypairs"],
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "no-kp" in msg
    assert raised
    return


def test_instance_vpn_join_unknown_provider_raises() -> None:
    env = _establish_instance_env()
    data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
             "subnet": "sub-a",
             "vpn_join": {"provider": "no-provider",
                          "control_plane_credential": "ts-prov-oauth",
                          "hostname_template": "{name}-lab"}}]
    raised = False
    try:
        load_cloud_instances_block(
            data=data,
            images=env["images"],
            subnets=env["subnets"],
            security_groups=env["security_groups"],
            keypairs=env["keypairs"],
            vpn_block=VPN_BLOCK,
            credential_lookup=CRED_LOOKUP,
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "no-provider" in msg
        assert "vpn.providers" in msg
    assert raised
    return


def test_instance_vpn_join_unresolved_credential_raises() -> None:
    env = _establish_instance_env()
    data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
             "subnet": "sub-a",
             "vpn_join": {"provider": "lab-tailnet",
                          "control_plane_credential": "no-such",
                          "hostname_template": "{name}-lab"}}]
    raised = False
    try:
        load_cloud_instances_block(
            data=data,
            images=env["images"],
            subnets=env["subnets"],
            security_groups=env["security_groups"],
            keypairs=env["keypairs"],
            vpn_block=VPN_BLOCK,
            credential_lookup=CRED_LOOKUP,
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "no-such" in msg
    assert raised
    return


def test_instance_with_valid_vpn_join_parses() -> None:
    env = _establish_instance_env()
    data = [{"name": "i1", "image": "ubuntu-24", "size": "small",
             "subnet": "sub-a",
             "vpn_join": {"provider": "lab-tailnet",
                          "control_plane_credential": "ts-prov-oauth",
                          "advertise_tags": ["tag:lab"],
                          "hostname_template": "{name}-lab"}}]
    instances = load_cloud_instances_block(
        data=data,
        images=env["images"],
        subnets=env["subnets"],
        security_groups=env["security_groups"],
        keypairs=env["keypairs"],
        vpn_block=VPN_BLOCK,
        credential_lookup=CRED_LOOKUP,
    )
    assert len(instances) == 1
    assert isinstance(instances[0], CloudInstanceSpec)
    assert isinstance(instances[0].vpn_join, VPNJoinSpec)
    assert instances[0].vpn_join.control_plane_credential == "ts-prov-oauth"
    return


def test_volume_without_size_or_existing_raises() -> None:
    data = [{"name": "vol1", "kind": "block"}]
    raised = False
    try:
        load_cloud_volumes_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "size_gb" in msg
        assert "existing_id" in msg
    assert raised
    return


def test_volume_unknown_kind_rejected() -> None:
    data = [{"name": "vol1", "kind": "magnetic", "size_gb": 10}]
    raised = False
    try:
        load_cloud_volumes_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "magnetic" in msg
    assert raised
    return


def test_unknown_record_type_rejected() -> None:
    data = [{"name": "x", "record_type": "QQQ", "values": ["1.2.3.4"]}]
    raised = False
    try:
        load_cloud_dns_records_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "QQQ" in msg
    assert raised
    return


def test_empty_values_rejected() -> None:
    data = [{"name": "x", "record_type": "A", "values": []}]
    raised = False
    try:
        load_cloud_dns_records_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "values" in msg
    assert raised
    return


def test_lb_unknown_target_raises() -> None:
    subnets = [CloudSubnetSpec(name="sub-a", network="lab-vpc",
                               cidr="10.0.1.0/24", zone="us-east-1a")]
    data = [{"name": "lb1", "scheme": "internet-facing",
             "subnet": "sub-a", "targets": ["ghost"]}]
    raised = False
    try:
        load_cloud_load_balancers_block(
            data=data, subnets=subnets, instances=[]
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "ghost" in msg
    assert raised
    return


def test_venues_forwarded_verbatim() -> None:
    data = {"aws-primary": {"some_key": 1, "nested": {"x": "y"}}}
    venues = load_cloud_venues_block(data=data)
    assert len(venues) == 1
    assert venues[0].name == "aws-primary"
    assert venues[0].overrides == {"some_key": 1,
                                   "nested": {"x": "y"}}
    return


def test_missing_region_raises() -> None:
    data = [{"name": "b1"}]
    raised = False
    try:
        load_cloud_buckets_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "region" in msg
    assert raised
    return


def test_accelerator_references_unknown_instance_fails() -> None:
    instances = _establish_accelerator_instances()
    data = [
        {"instance_name": "ghost-instance",
         "accelerators": [
             {"kind": "GPU", "model": "H100_SXM", "count": 8,
              "memory_gb": 80},
         ]},
    ]
    raised = False
    try:
        load_cloud_accelerators_block(
            data=data, instances=instances
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "ghost-instance" in msg
        assert "instance_name" in msg
        assert "devices[*].name" in msg
    assert raised
    return


def test_accelerator_valid_reference_parses() -> None:
    instances = _establish_accelerator_instances()
    data = [
        {"instance_name": "trainer-01",
         "accelerators": [
             {"kind": "GPU", "model": "H100_SXM", "count": 8,
              "interconnect": "NVSWITCH", "memory_gb": 80},
         ]},
    ]
    assignments = load_cloud_accelerators_block(
        data=data, instances=instances
    )
    assert len(assignments) == 1
    assert isinstance(assignments[0], CloudAcceleratorAssignment)
    assert assignments[0].instance_name == "trainer-01"
    assert assignments[0].accelerators[0].model == "H100_SXM"
    return


def test_accelerator_unknown_catalog_model_fails() -> None:
    instances = _establish_accelerator_instances()
    catalog = FakeAcceleratorCatalog(names=["H100_SXM"])
    data = [
        {"instance_name": "trainer-01",
         "accelerators": [
             {"kind": "GPU", "model": "MADE_UP_GPU", "count": 1,
              "memory_gb": 40},
         ]},
    ]
    raised = False
    try:
        load_cloud_accelerators_block(
            data=data, instances=instances,
            accelerator_catalog=catalog,
        )
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "MADE_UP_GPU" in msg
        assert "catalog" in msg
    assert raised
    return


def test_shared_fs_attach_or_provision_discriminator() -> None:
    # Neither size_tb nor existing_id present -- must fail.
    data = [{"name": "scratch-fs", "kind": "LUSTRE"}]
    raised = False
    try:
        load_cloud_shared_filesystems_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "size_tb" in msg
        assert "existing_id" in msg
    assert raised
    return


def test_shared_fs_provision_mode_parses() -> None:
    data = [{"name": "scratch-fs", "kind": "LUSTRE", "size_tb": 10}]
    filesystems = load_cloud_shared_filesystems_block(data=data)
    assert len(filesystems) == 1
    assert isinstance(filesystems[0], CloudSharedFilesystem)
    assert filesystems[0].size_tb == 10
    return


def test_shared_fs_attach_mode_parses() -> None:
    data = [{"name": "scratch-fs", "kind": "EFS",
             "existing_id": "fs-0abc123"}]
    filesystems = load_cloud_shared_filesystems_block(data=data)
    assert len(filesystems) == 1
    assert filesystems[0].existing_id == "fs-0abc123"
    return


def test_shared_fs_unknown_kind_rejected() -> None:
    data = [{"name": "scratch-fs", "kind": "NOTAFS", "size_tb": 1}]
    raised = False
    try:
        load_cloud_shared_filesystems_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "NOTAFS" in msg
    assert raised
    return


def test_dns_record_non_numeric_ttl_raises_configuration_error() -> None:
    data = [{"name": "web.example.com", "record_type": "A",
             "values": ["192.0.2.1"], "ttl": "not-a-number"}]
    raised = False
    try:
        load_cloud_dns_records_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "ttl" in msg
    assert raised
    return


def test_accelerator_requires_memory_gb() -> None:
    data = [{"instance_name": "i1",
             "accelerators": [{"kind": "GPU", "model": "H100_SXM",
                               "count": 8}]}]
    raised = False
    try:
        load_cloud_accelerators_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "memory_gb" in msg
    assert raised
    return


def test_accelerator_non_numeric_count_raises() -> None:
    data = [{"instance_name": "i1",
             "accelerators": [{"kind": "GPU", "model": "H100_SXM",
                               "count": "many", "memory_gb": 80}]}]
    raised = False
    try:
        load_cloud_accelerators_block(data=data)
    except ConfigurationError as ctx_exception:
        raised = True
        msg = str(ctx_exception)
        assert "count" in msg
    assert raised
    return


def test_cloud_keys_registered() -> None:
    expected = (
        "networks", "subnets", "security_groups", "keypairs", "images",
        "instances", "volumes", "buckets", "load_balancers", "dns_records",
        "accelerators", "shared_filesystems",
    )
    for key in expected:
        assert key in TOP_LEVEL_SCHEMA_LOADERS
    return

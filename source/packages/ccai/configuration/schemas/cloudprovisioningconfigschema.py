"""
.. module:: cloudprovisioningconfigschema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Schema fragments for the cloud-provisioning top-level blocks
        (``networks``, ``subnets``, ``security_groups``, ``keypairs``,
        ``images``, ``instances``, ``volumes``, ``buckets``,
        ``load_balancers``, ``dns_records``, and per-venue overrides).

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import ipaddress
import logging
import os

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ccai.errors.exceptions import ConfigurationError

from ccai.configuration.schemas.vpnconfigschema import VPNBlock

# ---------------------------------------------------------------------------
# Cross-repository type imports.
#
# The canonical model classes live in ``codecraftai-provisioning``. They are
# imported hard so that a missing or mis-pathed core dependency fails loudly
# at import time rather than silently substituting a structurally divergent
# local stand-in (the previous fallback ``VPNJoinSpec`` made
# ``hostname_template`` optional while the canonical class requires it).
# ---------------------------------------------------------------------------

from ccai.interfaces.schemavalidationerror import SchemaValidationError
from ccai.interfaces.vpnjoinspec import VPNJoinSpec
from ccai.interfaces.cloudacceleratorspec import (
    CloudAcceleratorSpec,
)
from ccai.interfaces.sharedfsmountspec import SharedFsMountSpec
from ccai.interfaces.cloudsharedfilesystem import (
    CloudSharedFilesystem,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enum-like literal sets.
# ---------------------------------------------------------------------------

SUPPORTED_VPN_PROVIDERS_FOR_JOIN: Tuple[str, ...] = ("tailscale", "twingate")

SUPPORTED_ACCELERATOR_KINDS: Tuple[str, ...] = ("GPU", "TPU", "IPU", "ASIC")

SUPPORTED_ACCELERATOR_INTERCONNECTS: Tuple[str, ...] = (
    "NONE", "PCIE", "NVLINK", "NVSWITCH", "INFINITY_FABRIC",
)

SUPPORTED_SHARED_FS_KINDS: Tuple[str, ...] = (
    "WEKA", "LUSTRE", "VAST", "GPFS", "EFS",
    "FILESTORE", "AZUREFILES", "BEEGFS", "VENUE_NATIVE",
)

SUPPORTED_VOLUME_KINDS: Tuple[str, ...] = ("block", "object", "shared")

SUPPORTED_LB_SCHEMES: Tuple[str, ...] = ("internet-facing", "internal")

SUPPORTED_DNS_RECORD_TYPES: Tuple[str, ...] = (
    "A", "AAAA", "CNAME", "TXT", "MX", "SRV",
)

SUPPORTED_INGRESS_PROTOCOLS: Tuple[str, ...] = ("tcp", "udp", "icmp", "-1")


# ---------------------------------------------------------------------------
# Dataclasses for each top-level block entry.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CloudNetworkSpec:
    """
        Typed representation of a ``networks[*]`` entry.

        :param name: Unique network identifier within the spec.
        :param cidr: The IPv4 CIDR block for the network.
        :param region: The cloud region in which the network lives.
        :param tags: Optional list of single-key tag dicts.
    """
    name: str
    cidr: str
    region: str
    tags: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class CloudSubnetSpec:
    """
        Typed representation of a ``subnets[*]`` entry.

        :param name: Unique subnet identifier within the spec.
        :param network: Name of a ``networks[*]`` entry the subnet belongs to.
        :param cidr: The subnet IPv4 CIDR.
        :param zone: Availability zone identifier.
        :param public: ``True`` when the subnet is internet-routable.
    """
    name: str
    network: str
    cidr: str
    zone: str
    public: bool = False


@dataclass(frozen=True)
class CloudSecurityGroupRule:
    """
        Typed representation of an ingress / egress rule.

        :param protocol: Wire protocol (``tcp``, ``udp``, ``icmp`` or ``-1``).
        :param from_port: Lower bound of the port range.
        :param to_port: Upper bound of the port range.
        :param source_cidrs: List of source CIDR blocks.
        :param description: Optional human-readable description.
    """
    protocol: str
    from_port: int
    to_port: int
    source_cidrs: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass(frozen=True)
class CloudSecurityGroupSpec:
    """
        Typed representation of a ``security_groups[*]`` entry.

        :param name: Unique security-group identifier.
        :param network: Name of the parent ``networks[*]`` entry.
        :param ingress_rules: List of ingress rules.
        :param egress_rules: List of egress rules.
    """
    name: str
    network: str
    ingress_rules: List[CloudSecurityGroupRule] = field(default_factory=list)
    egress_rules: List[CloudSecurityGroupRule] = field(default_factory=list)


@dataclass(frozen=True)
class CloudKeyPairSpec:
    """
        Typed representation of a ``keypairs[*]`` entry.

        :param name: Unique keypair identifier.
        :param public_key: PEM-encoded public-key material.
    """
    name: str
    public_key: str


@dataclass(frozen=True)
class CloudImageSpec:
    """
        Typed representation of an ``images[*]`` entry.

        :param name: Unique image identifier.
        :param family: Image family identifier (e.g. ``ubuntu``).
        :param version: Image version string (e.g. ``24.04``).
        :param architecture: CPU architecture identifier.
    """
    name: str
    family: str
    version: str
    architecture: str = "x86_64"


@dataclass(frozen=True)
class CloudInstanceSpec:
    """
        Typed representation of an ``instances[*]`` entry.

        :param name: Unique instance identifier.
        :param image: Name of an ``images[*]`` entry.
        :param size: Provider-neutral instance size token.
        :param subnet: Name of a ``subnets[*]`` entry.
        :param security_groups: Names of ``security_groups[*]`` entries.
        :param keypair: Name of a ``keypairs[*]`` entry.
        :param public_ip: ``True`` to allocate a public IP.
        :param vpn_join: Optional ``VPNJoinSpec`` describing overlay join.
        :param tags: Optional list of single-key tag dicts.
    """
    name: str
    image: str
    size: str
    subnet: str
    security_groups: List[str] = field(default_factory=list)
    keypair: Optional[str] = None
    public_ip: bool = False
    vpn_join: Optional[VPNJoinSpec] = None
    tags: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class CloudVolumeSpec:
    """
        Typed representation of a ``volumes[*]`` entry.

        :param name: Unique volume identifier.
        :param kind: One of ``block``, ``object``, ``shared``.
        :param size_gb: Optional size in GB (required when not attaching
            an existing volume).
        :param existing_id: Optional identifier of an existing volume to
            attach.
        :param zone: Optional availability zone for the volume.
    """
    name: str
    kind: str
    size_gb: Optional[int] = None
    existing_id: Optional[str] = None
    zone: Optional[str] = None


@dataclass(frozen=True)
class CloudBucketSpec:
    """
        Typed representation of a ``buckets[*]`` entry.

        :param name: Unique bucket identifier.
        :param region: Region in which the bucket is provisioned.
        :param versioning: ``True`` when object versioning is enabled.
    """
    name: str
    region: str
    versioning: bool = False


@dataclass(frozen=True)
class CloudLoadBalancerSpec:
    """
        Typed representation of a ``load_balancers[*]`` entry.

        :param name: Unique LB identifier.
        :param scheme: ``internet-facing`` or ``internal``.
        :param subnet: Name of the subnet hosting the LB.
        :param targets: Names of ``instances[*]`` entries behind the LB.
    """
    name: str
    scheme: str
    subnet: str
    targets: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CloudDnsRecordSpec:
    """
        Typed representation of a ``dns_records[*]`` entry.

        :param name: DNS record name (FQDN or short).
        :param record_type: DNS record type (``A``, ``CNAME``, ...).
        :param values: List of record values.
        :param ttl: Time-to-live in seconds.
    """
    name: str
    record_type: str
    values: List[str] = field(default_factory=list)
    ttl: int = 300


@dataclass(frozen=True)
class CloudAcceleratorAssignment:
    """
        Typed representation of an ``accelerators[*]`` entry.

        Each entry binds one declared instance to a list of venue-neutral
        accelerator specifications.

        :param instance_name: Name of a declared ``devices[*]`` /
            ``instances[*]`` entry the accelerators are attached to.
        :param accelerators: List of ``CloudAcceleratorSpec`` descriptors.
    """
    instance_name: str
    accelerators: List[CloudAcceleratorSpec] = field(default_factory=list)


@dataclass(frozen=True)
class CloudVenueOverrides:
    """
        Typed representation of ``venues.<name>:`` override block.

        :param name: Venue identifier.
        :param overrides: Opaque dict forwarded to the venue plugin.
    """
    name: str
    overrides: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CloudProvisioningBlock:
    """
        Typed aggregate of every cloud-provisioning block.

        :param networks: Parsed networks.
        :param subnets: Parsed subnets.
        :param security_groups: Parsed security groups.
        :param keypairs: Parsed keypairs.
        :param images: Parsed images.
        :param instances: Parsed instances.
        :param volumes: Parsed volumes.
        :param buckets: Parsed buckets.
        :param load_balancers: Parsed load balancers.
        :param dns_records: Parsed DNS records.
        :param accelerators: Parsed accelerator assignments.
        :param shared_filesystems: Parsed shared filesystems.
        :param venues: Parsed per-venue overrides.
    """
    networks: List[CloudNetworkSpec] = field(default_factory=list)
    subnets: List[CloudSubnetSpec] = field(default_factory=list)
    security_groups: List[CloudSecurityGroupSpec] = field(default_factory=list)
    keypairs: List[CloudKeyPairSpec] = field(default_factory=list)
    images: List[CloudImageSpec] = field(default_factory=list)
    instances: List[CloudInstanceSpec] = field(default_factory=list)
    volumes: List[CloudVolumeSpec] = field(default_factory=list)
    buckets: List[CloudBucketSpec] = field(default_factory=list)
    load_balancers: List[CloudLoadBalancerSpec] = field(default_factory=list)
    dns_records: List[CloudDnsRecordSpec] = field(default_factory=list)
    accelerators: List[CloudAcceleratorAssignment] = field(default_factory=list)
    shared_filesystems: List[CloudSharedFilesystem] = field(default_factory=list)
    venues: List[CloudVenueOverrides] = field(default_factory=list)


CredentialLookup = Callable[[str], Optional[Any]]


# ---------------------------------------------------------------------------
# Validation helpers.
# ---------------------------------------------------------------------------

def _require_mapping(*, entry: Any, path: str, err_lines: List[str]) -> bool:
    """
        Asserts that ``entry`` is a mapping, appending an error on failure.

        :param entry: The candidate value.
        :param path: YAML-like path used in the error message.
        :param err_lines: Mutable list of error lines.

        :returns: ``True`` when ``entry`` is a dict, ``False`` otherwise.
    """
    if not isinstance(entry, dict):
        err_lines.append(f"{path} must be a mapping.")
        rtnval = False
        return rtnval
    rtnval = True
    return rtnval


def _require_keys(*, entry: dict, required: Tuple[str, ...], path: str,
                  err_lines: List[str]) -> bool:
    """
        Asserts that every required key is present on ``entry``.

        :param entry: The dict to check.
        :param required: Tuple of required key names.
        :param path: YAML-like path used in the error message.
        :param err_lines: Mutable list of error lines.

        :returns: ``True`` when all required keys are present.
    """
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


def _validate_cidr(*, raw: Any, path: str, err_lines: List[str]) -> Optional[str]:
    """
        Validates that ``raw`` parses as an IPv4 / IPv6 network CIDR.

        :param raw: The candidate CIDR string.
        :param path: YAML-like path used in the error message.
        :param err_lines: Mutable list of error lines.

        :returns: The original string on success, or ``None`` on failure.
    """
    if not isinstance(raw, str):
        err_lines.append(f"{path} must be a CIDR string.")
        rtnval = None
        return rtnval
    try:
        ipaddress.ip_network(raw, strict=False)
    except (ValueError, TypeError):
        err_lines.append(f"{path}={raw!r} is not a valid CIDR.")
        rtnval = None
        return rtnval
    rtnval = raw
    return rtnval


def _validate_enum(*, raw: Any, accepted: Tuple[str, ...], path: str,
                   err_lines: List[str]) -> Optional[str]:
    """
        Validates that ``raw`` is a member of ``accepted``.

        :param raw: The candidate value.
        :param accepted: Tuple of accepted values.
        :param path: YAML-like path used in the error message.
        :param err_lines: Mutable list of error lines.

        :returns: ``raw`` on success, ``None`` otherwise.
    """
    if raw not in accepted:
        err_lines.append(
            f"{path}={raw!r} must be one of {list(accepted)!r}."
        )
        rtnval = None
        return rtnval
    rtnval = raw
    return rtnval


def _validate_int(*, raw: Any, path: str, err_lines: List[str],
                  positive: bool = False) -> Optional[int]:
    """
        Converts ``raw`` to an ``int``, accumulating an error on failure
        instead of letting a ``ValueError`` / ``TypeError`` escape.

        :param raw: The candidate value.
        :param path: YAML-like path used in the error message.
        :param err_lines: Mutable list of error lines.
        :param positive: When ``True`` the converted value must be > 0.

        :returns: The converted ``int`` on success, ``None`` otherwise.
    """
    if isinstance(raw, bool):
        err_lines.append(f"{path}={raw!r} must be an integer.")
        rtnval = None
        return rtnval
    try:
        converted = int(raw)
    except (ValueError, TypeError):
        err_lines.append(f"{path}={raw!r} must be an integer.")
        rtnval = None
        return rtnval
    if positive and converted <= 0:
        err_lines.append(f"{path}={converted} must be greater than 0.")
        rtnval = None
        return rtnval
    rtnval = converted
    return rtnval


def _normalise_tags(*, raw: Any, path: str,
                    err_lines: List[str]) -> Optional[Dict[str, Any]]:
    """
        Normalises a ``tags`` value to a flat ``Dict[str, Any]``.

        Accepts either an already-flat mapping or a list of single-key
        tag dicts (the historical config convention). ``None`` yields an
        empty dict.

        :param raw: The candidate ``tags`` value.
        :param path: YAML-like path used in the error message.
        :param err_lines: Mutable list of error lines.

        :returns: A flat dict on success, ``None`` on failure.
    """
    if raw is None:
        rtnval = {}
        return rtnval
    if isinstance(raw, dict):
        rtnval = dict(raw)
        return rtnval
    if isinstance(raw, list):
        flattened: Dict[str, Any] = {}
        for tag_entry in raw:
            if not isinstance(tag_entry, dict):
                err_lines.append(
                    f"{path} list entries must be single-key mappings."
                )
                rtnval = None
                return rtnval
            for key, value in tag_entry.items():
                flattened[key] = value
        rtnval = flattened
        return rtnval
    err_lines.append(f"{path} must be a mapping or a list of mappings.")
    rtnval = None
    return rtnval


# ---------------------------------------------------------------------------
# Per-block loaders.
# ---------------------------------------------------------------------------

def load_cloud_networks_block(*, data: Optional[list] = None) -> List[CloudNetworkSpec]:
    """
        Parses and validates the ``networks:`` block.

        :param data: The raw list value of the ``networks:`` key.

        :returns: List of parsed ``CloudNetworkSpec`` instances.
        :raises: ConfigurationError when any entry is malformed.
    """
    err_lines: List[str] = []
    rtnval = _parse_networks(data=data, err_lines=err_lines)
    _raise_if_errors(label="networks", err_lines=err_lines)
    return rtnval


def _parse_networks(*, data: Optional[list],
                    err_lines: List[str]) -> List[CloudNetworkSpec]:
    rtnval: List[CloudNetworkSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("networks must be a list.")
        return rtnval
    for idx, entry in enumerate(raw_list):
        path = f"networks[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "cidr", "region"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        cidr = _validate_cidr(
            raw=entry["cidr"], path=f"{path}.cidr", err_lines=err_lines
        )
        if cidr is None:
            continue
        spec = CloudNetworkSpec(
            name=entry["name"],
            cidr=cidr,
            region=entry["region"],
            tags=list(entry.get("tags", [])),
        )
        rtnval.append(spec)
    return rtnval


def load_cloud_subnets_block(*, data: Optional[list] = None,
                             networks: Optional[List[CloudNetworkSpec]] = None
                             ) -> List[CloudSubnetSpec]:
    """
        Parses and validates the ``subnets:`` block.

        :param data: The raw list value of the ``subnets:`` key.
        :param networks: List of already-parsed networks used for
            cross-reference validation.

        :returns: List of parsed ``CloudSubnetSpec`` instances.
        :raises: ConfigurationError when any entry is malformed or
            references an unknown network.
    """
    err_lines: List[str] = []
    networks_ref = networks if networks is not None else []
    rtnval = _parse_subnets(
        data=data, networks=networks_ref, err_lines=err_lines
    )
    _raise_if_errors(label="subnets", err_lines=err_lines)
    return rtnval


def _parse_subnets(*, data: Optional[list], networks: List[CloudNetworkSpec],
                   err_lines: List[str]) -> List[CloudSubnetSpec]:
    rtnval: List[CloudSubnetSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("subnets must be a list.")
        return rtnval
    known_networks = {n.name for n in networks}
    for idx, entry in enumerate(raw_list):
        path = f"subnets[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "network", "cidr", "zone"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        cidr = _validate_cidr(
            raw=entry["cidr"], path=f"{path}.cidr", err_lines=err_lines
        )
        if cidr is None:
            continue
        network_name = entry["network"]
        if network_name not in known_networks:
            err_lines.append(
                f"{path}.network={network_name!r} does not reference any "
                f"declared networks[*].name."
            )
            continue
        spec = CloudSubnetSpec(
            name=entry["name"],
            network=network_name,
            cidr=cidr,
            zone=entry["zone"],
            public=bool(entry.get("public", False)),
        )
        rtnval.append(spec)
    return rtnval


def load_cloud_security_groups_block(*, data: Optional[list] = None,
                                     networks: Optional[List[CloudNetworkSpec]] = None
                                     ) -> List[CloudSecurityGroupSpec]:
    """
        Parses and validates the ``security_groups:`` block.

        :param data: The raw list value of the ``security_groups:`` key.
        :param networks: List of already-parsed networks used for
            cross-reference validation.

        :returns: List of parsed ``CloudSecurityGroupSpec`` instances.
        :raises: ConfigurationError when validation fails.
    """
    err_lines: List[str] = []
    networks_ref = networks if networks is not None else []
    rtnval = _parse_security_groups(
        data=data, networks=networks_ref, err_lines=err_lines
    )
    _raise_if_errors(label="security_groups", err_lines=err_lines)
    return rtnval


def _parse_security_groups(*, data: Optional[list],
                           networks: List[CloudNetworkSpec],
                           err_lines: List[str]
                           ) -> List[CloudSecurityGroupSpec]:
    rtnval: List[CloudSecurityGroupSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("security_groups must be a list.")
        return rtnval
    known_networks = {n.name for n in networks}
    for idx, entry in enumerate(raw_list):
        path = f"security_groups[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "network"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        network_name = entry["network"]
        if network_name not in known_networks:
            err_lines.append(
                f"{path}.network={network_name!r} does not reference any "
                f"declared networks[*].name."
            )
            continue
        ingress = _parse_sg_rules(
            raw=entry.get("ingress_rules", []),
            path=f"{path}.ingress_rules",
            err_lines=err_lines,
        )
        egress = _parse_sg_rules(
            raw=entry.get("egress_rules", []),
            path=f"{path}.egress_rules",
            err_lines=err_lines,
        )
        spec = CloudSecurityGroupSpec(
            name=entry["name"],
            network=network_name,
            ingress_rules=ingress,
            egress_rules=egress,
        )
        rtnval.append(spec)
    return rtnval


def _parse_sg_rules(*, raw: Any, path: str,
                    err_lines: List[str]) -> List[CloudSecurityGroupRule]:
    rtnval: List[CloudSecurityGroupRule] = []
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
            required=("protocol", "from_port", "to_port"),
            path=item_path,
            err_lines=err_lines,
        ):
            continue
        protocol = _validate_enum(
            raw=entry["protocol"],
            accepted=SUPPORTED_INGRESS_PROTOCOLS,
            path=f"{item_path}.protocol",
            err_lines=err_lines,
        )
        if protocol is None:
            continue
        from_port = _validate_int(
            raw=entry["from_port"], path=f"{item_path}.from_port",
            err_lines=err_lines,
        )
        to_port = _validate_int(
            raw=entry["to_port"], path=f"{item_path}.to_port",
            err_lines=err_lines,
        )
        if from_port is None or to_port is None:
            continue
        rule = CloudSecurityGroupRule(
            protocol=protocol,
            from_port=from_port,
            to_port=to_port,
            source_cidrs=list(entry.get("source_cidrs", [])),
            description=entry.get("description"),
        )
        rtnval.append(rule)
    return rtnval


def load_cloud_keypairs_block(*, data: Optional[list] = None
                              ) -> List[CloudKeyPairSpec]:
    """
        Parses and validates the ``keypairs:`` block.

        :param data: The raw list value of the ``keypairs:`` key.

        :returns: List of parsed ``CloudKeyPairSpec`` instances.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    rtnval = _parse_keypairs(data=data, err_lines=err_lines)
    _raise_if_errors(label="keypairs", err_lines=err_lines)
    return rtnval


def _parse_keypairs(*, data: Optional[list],
                    err_lines: List[str]) -> List[CloudKeyPairSpec]:
    rtnval: List[CloudKeyPairSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("keypairs must be a list.")
        return rtnval
    for idx, entry in enumerate(raw_list):
        path = f"keypairs[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "public_key"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        spec = CloudKeyPairSpec(
            name=entry["name"],
            public_key=entry["public_key"],
        )
        rtnval.append(spec)
    return rtnval


def load_cloud_images_block(*, data: Optional[list] = None
                            ) -> List[CloudImageSpec]:
    """
        Parses and validates the ``images:`` block.

        :param data: The raw list value of the ``images:`` key.

        :returns: List of parsed ``CloudImageSpec`` instances.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    rtnval = _parse_images(data=data, err_lines=err_lines)
    _raise_if_errors(label="images", err_lines=err_lines)
    return rtnval


def _parse_images(*, data: Optional[list],
                  err_lines: List[str]) -> List[CloudImageSpec]:
    rtnval: List[CloudImageSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("images must be a list.")
        return rtnval
    for idx, entry in enumerate(raw_list):
        path = f"images[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "family", "version"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        spec = CloudImageSpec(
            name=entry["name"],
            family=entry["family"],
            version=str(entry["version"]),
            architecture=entry.get("architecture", "x86_64"),
        )
        rtnval.append(spec)
    return rtnval


def load_cloud_instances_block(*, data: Optional[list] = None,
                               images: Optional[List[CloudImageSpec]] = None,
                               subnets: Optional[List[CloudSubnetSpec]] = None,
                               security_groups: Optional[List[CloudSecurityGroupSpec]] = None,
                               keypairs: Optional[List[CloudKeyPairSpec]] = None,
                               vpn_block: Optional[VPNBlock] = None,
                               credential_lookup: Optional[CredentialLookup] = None
                               ) -> List[CloudInstanceSpec]:
    """
        Parses and validates the ``instances:`` block.

        :param data: The raw list value of the ``instances:`` key.
        :param images: Already-parsed images for cross-reference.
        :param subnets: Already-parsed subnets for cross-reference.
        :param security_groups: Already-parsed security groups for
            cross-reference.
        :param keypairs: Already-parsed keypairs for cross-reference.
        :param vpn_block: Optional ``VPNBlock`` used to resolve
            ``vpn_join`` provider references.
        :param credential_lookup: Optional callable resolving
            ``vpn_join.control_plane_credential`` identifiers.

        :returns: List of parsed ``CloudInstanceSpec`` instances.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    images_ref = images if images is not None else []
    subnets_ref = subnets if subnets is not None else []
    sg_ref = security_groups if security_groups is not None else []
    keypairs_ref = keypairs if keypairs is not None else []
    rtnval = _parse_instances(
        data=data,
        images=images_ref,
        subnets=subnets_ref,
        security_groups=sg_ref,
        keypairs=keypairs_ref,
        vpn_block=vpn_block,
        credential_lookup=credential_lookup,
        err_lines=err_lines,
    )
    _raise_if_errors(label="instances", err_lines=err_lines)
    return rtnval


def _parse_instances(*, data: Optional[list],
                     images: List[CloudImageSpec],
                     subnets: List[CloudSubnetSpec],
                     security_groups: List[CloudSecurityGroupSpec],
                     keypairs: List[CloudKeyPairSpec],
                     vpn_block: Optional[VPNBlock],
                     credential_lookup: Optional[CredentialLookup],
                     err_lines: List[str]) -> List[CloudInstanceSpec]:
    rtnval: List[CloudInstanceSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("instances must be a list.")
        return rtnval
    known_images = {i.name for i in images}
    known_subnets = {s.name for s in subnets}
    known_sgs = {g.name for g in security_groups}
    known_keypairs = {k.name for k in keypairs}
    # Maps an overlay-profile name to its provider kind ("tailscale" /
    # "twingate"). The canonical VPNJoinSpec stores the provider kind, not
    # the profile name, so the kind is resolved here from the VPN block.
    vpn_profile_kinds: Dict[str, str] = {}
    if vpn_block is not None:
        for profile in vpn_block.providers:
            vpn_profile_kinds[profile.name] = profile.provider
    for idx, entry in enumerate(raw_list):
        path = f"instances[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "image", "size", "subnet"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        image_name = entry["image"]
        if image_name not in known_images:
            err_lines.append(
                f"{path}.image={image_name!r} does not reference any "
                f"declared images[*].name."
            )
            continue
        subnet_name = entry["subnet"]
        if subnet_name not in known_subnets:
            err_lines.append(
                f"{path}.subnet={subnet_name!r} does not reference any "
                f"declared subnets[*].name."
            )
            continue
        keypair_name = entry.get("keypair")
        if keypair_name is not None and keypair_name not in known_keypairs:
            err_lines.append(
                f"{path}.keypair={keypair_name!r} does not reference any "
                f"declared keypairs[*].name."
            )
            continue
        sg_names = list(entry.get("security_groups", []))
        sg_ok = True
        for sg_name in sg_names:
            if sg_name not in known_sgs:
                err_lines.append(
                    f"{path}.security_groups references {sg_name!r}, which "
                    f"is not in declared security_groups[*].name."
                )
                sg_ok = False
        if not sg_ok:
            continue
        vpn_join = _parse_vpn_join(
            raw=entry.get("vpn_join"),
            path=f"{path}.vpn_join",
            vpn_profile_kinds=vpn_profile_kinds,
            credential_lookup=credential_lookup,
            err_lines=err_lines,
        )
        spec = CloudInstanceSpec(
            name=entry["name"],
            image=image_name,
            size=entry["size"],
            subnet=subnet_name,
            security_groups=sg_names,
            keypair=keypair_name,
            public_ip=bool(entry.get("public_ip", False)),
            vpn_join=vpn_join,
            tags=list(entry.get("tags", [])),
        )
        rtnval.append(spec)
    return rtnval


def _parse_vpn_join(*, raw: Any, path: str,
                    vpn_profile_kinds: Dict[str, str],
                    credential_lookup: Optional[CredentialLookup],
                    err_lines: List[str]) -> Optional[VPNJoinSpec]:
    """
        Validates and constructs a single ``instances[*].vpn_join`` entry.

        ``vpn_join.provider`` references a ``vpn.providers[*].name`` overlay
        profile. The canonical ``VPNJoinSpec`` stores the provider *kind*
        (``tailscale`` / ``twingate``), so the kind is resolved here from
        ``vpn_profile_kinds``.

        :param raw: The raw ``vpn_join`` mapping, or ``None``.
        :param path: YAML-like path used in error messages.
        :param vpn_profile_kinds: Mapping of overlay-profile name to
            provider kind, built from the parsed VPN block.
        :param credential_lookup: Optional callable resolving the
            ``control_plane_credential`` identifier.
        :param err_lines: Mutable list of error lines.

        :returns: A ``VPNJoinSpec`` on success, ``None`` otherwise.
    """
    if raw is None:
        rtnval = None
        return rtnval
    if not _require_mapping(entry=raw, path=path, err_lines=err_lines):
        rtnval = None
        return rtnval
    if not _require_keys(
        entry=raw,
        required=("provider", "control_plane_credential", "hostname_template"),
        path=path,
        err_lines=err_lines,
    ):
        rtnval = None
        return rtnval
    provider_name = raw["provider"]
    provider_kind = provider_name
    if len(vpn_profile_kinds) > 0:
        if provider_name not in vpn_profile_kinds:
            err_lines.append(
                f"{path}.provider={provider_name!r} does not reference any "
                f"declared vpn.providers[*].name."
            )
            rtnval = None
            return rtnval
        provider_kind = vpn_profile_kinds[provider_name]
    cred_ref = raw["control_plane_credential"]
    if credential_lookup is not None:
        resolved = credential_lookup(cred_ref)
        if resolved is None:
            err_lines.append(
                f"{path}.control_plane_credential={cred_ref!r} did not "
                f"resolve to any known credential identifier."
            )
            rtnval = None
            return rtnval
    try:
        rtnval = VPNJoinSpec(
            provider=provider_kind,
            control_plane_credential=cred_ref,
            advertise_tags=list(raw.get("advertise_tags", [])),
            hostname_template=raw.get("hostname_template"),
            connector_only=bool(
                raw.get("connector_only", provider_kind == "twingate")
            ),
        )
    except SchemaValidationError as ex:
        err_lines.append(f"{path}: {ex}")
        rtnval = None

    return rtnval


def load_cloud_volumes_block(*, data: Optional[list] = None
                             ) -> List[CloudVolumeSpec]:
    """
        Parses and validates the ``volumes:`` block.

        :param data: The raw list value of the ``volumes:`` key.

        :returns: List of parsed ``CloudVolumeSpec`` instances.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    rtnval = _parse_volumes(data=data, err_lines=err_lines)
    _raise_if_errors(label="volumes", err_lines=err_lines)
    return rtnval


def _parse_volumes(*, data: Optional[list],
                   err_lines: List[str]) -> List[CloudVolumeSpec]:
    rtnval: List[CloudVolumeSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("volumes must be a list.")
        return rtnval
    for idx, entry in enumerate(raw_list):
        path = f"volumes[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "kind"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        kind = _validate_enum(
            raw=entry["kind"],
            accepted=SUPPORTED_VOLUME_KINDS,
            path=f"{path}.kind",
            err_lines=err_lines,
        )
        if kind is None:
            continue
        size_gb_raw = entry.get("size_gb")
        existing_id = entry.get("existing_id")
        if size_gb_raw is None and existing_id is None:
            err_lines.append(
                f"{path} must declare either 'size_gb' or 'existing_id'."
            )
            continue
        size_gb = None
        if size_gb_raw is not None:
            size_gb = _validate_int(
                raw=size_gb_raw, path=f"{path}.size_gb",
                err_lines=err_lines, positive=True,
            )
            if size_gb is None:
                continue
        spec = CloudVolumeSpec(
            name=entry["name"],
            kind=kind,
            size_gb=size_gb,
            existing_id=existing_id,
            zone=entry.get("zone"),
        )
        rtnval.append(spec)
    return rtnval


def load_cloud_buckets_block(*, data: Optional[list] = None
                             ) -> List[CloudBucketSpec]:
    """
        Parses and validates the ``buckets:`` block.

        :param data: The raw list value of the ``buckets:`` key.

        :returns: List of parsed ``CloudBucketSpec`` instances.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    rtnval = _parse_buckets(data=data, err_lines=err_lines)
    _raise_if_errors(label="buckets", err_lines=err_lines)
    return rtnval


def _parse_buckets(*, data: Optional[list],
                   err_lines: List[str]) -> List[CloudBucketSpec]:
    rtnval: List[CloudBucketSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("buckets must be a list.")
        return rtnval
    for idx, entry in enumerate(raw_list):
        path = f"buckets[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "region"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        spec = CloudBucketSpec(
            name=entry["name"],
            region=entry["region"],
            versioning=bool(entry.get("versioning", False)),
        )
        rtnval.append(spec)
    return rtnval


def load_cloud_load_balancers_block(*, data: Optional[list] = None,
                                    subnets: Optional[List[CloudSubnetSpec]] = None,
                                    instances: Optional[List[CloudInstanceSpec]] = None
                                    ) -> List[CloudLoadBalancerSpec]:
    """
        Parses and validates the ``load_balancers:`` block.

        :param data: The raw list value of the ``load_balancers:`` key.
        :param subnets: Already-parsed subnets for cross-reference.
        :param instances: Already-parsed instances for cross-reference.

        :returns: List of parsed ``CloudLoadBalancerSpec`` instances.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    subnets_ref = subnets if subnets is not None else []
    instances_ref = instances if instances is not None else []
    rtnval = _parse_load_balancers(
        data=data,
        subnets=subnets_ref,
        instances=instances_ref,
        err_lines=err_lines,
    )
    _raise_if_errors(label="load_balancers", err_lines=err_lines)
    return rtnval


def _parse_load_balancers(*, data: Optional[list],
                          subnets: List[CloudSubnetSpec],
                          instances: List[CloudInstanceSpec],
                          err_lines: List[str]
                          ) -> List[CloudLoadBalancerSpec]:
    rtnval: List[CloudLoadBalancerSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("load_balancers must be a list.")
        return rtnval
    known_subnets = {s.name for s in subnets}
    known_instances = {i.name for i in instances}
    for idx, entry in enumerate(raw_list):
        path = f"load_balancers[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "scheme", "subnet"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        scheme = _validate_enum(
            raw=entry["scheme"],
            accepted=SUPPORTED_LB_SCHEMES,
            path=f"{path}.scheme",
            err_lines=err_lines,
        )
        if scheme is None:
            continue
        subnet_name = entry["subnet"]
        if subnet_name not in known_subnets:
            err_lines.append(
                f"{path}.subnet={subnet_name!r} does not reference any "
                f"declared subnets[*].name."
            )
            continue
        targets = list(entry.get("targets", []))
        targets_ok = True
        for tgt in targets:
            if tgt not in known_instances:
                err_lines.append(
                    f"{path}.targets references {tgt!r}, which is not in "
                    f"declared instances[*].name."
                )
                targets_ok = False
        if not targets_ok:
            continue
        spec = CloudLoadBalancerSpec(
            name=entry["name"],
            scheme=scheme,
            subnet=subnet_name,
            targets=targets,
        )
        rtnval.append(spec)
    return rtnval


def load_cloud_dns_records_block(*, data: Optional[list] = None
                                 ) -> List[CloudDnsRecordSpec]:
    """
        Parses and validates the ``dns_records:`` block.

        :param data: The raw list value of the ``dns_records:`` key.

        :returns: List of parsed ``CloudDnsRecordSpec`` instances.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    rtnval = _parse_dns_records(data=data, err_lines=err_lines)
    _raise_if_errors(label="dns_records", err_lines=err_lines)
    return rtnval


def _parse_dns_records(*, data: Optional[list],
                       err_lines: List[str]) -> List[CloudDnsRecordSpec]:
    rtnval: List[CloudDnsRecordSpec] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("dns_records must be a list.")
        return rtnval
    for idx, entry in enumerate(raw_list):
        path = f"dns_records[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "record_type", "values"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        record_type = _validate_enum(
            raw=entry["record_type"],
            accepted=SUPPORTED_DNS_RECORD_TYPES,
            path=f"{path}.record_type",
            err_lines=err_lines,
        )
        if record_type is None:
            continue
        values = list(entry.get("values", []))
        if len(values) == 0:
            err_lines.append(
                f"{path}.values must be a non-empty list."
            )
            continue
        ttl = _validate_int(
            raw=entry.get("ttl", 300), path=f"{path}.ttl",
            err_lines=err_lines, positive=True,
        )
        if ttl is None:
            continue
        spec = CloudDnsRecordSpec(
            name=entry["name"],
            record_type=record_type,
            values=values,
            ttl=ttl,
        )
        rtnval.append(spec)
    return rtnval


def load_cloud_accelerators_block(*, data: Optional[list] = None,
                                  instances: Optional[List[CloudInstanceSpec]] = None,
                                  accelerator_catalog: Optional[Any] = None
                                  ) -> List[CloudAcceleratorAssignment]:
    """
        Parses and validates the ``accelerators:`` block.

        Each entry binds an instance to a list of venue-neutral accelerator
        specifications. The ``instance_name`` is cross-referenced against the
        declared instances / devices, and each accelerator's ``model`` neutral
        name is cross-referenced against the accelerator catalog when one is
        supplied.

        :param data: The raw list value of the ``accelerators:`` key.
        :param instances: Already-parsed instances used to validate
            ``instance_name`` cross-references.
        :param accelerator_catalog: Optional ``CloudAcceleratorCatalog`` used
            to validate accelerator ``model`` neutral names.

        :returns: List of parsed ``CloudAcceleratorAssignment`` instances.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    instances_ref = instances if instances is not None else []
    rtnval = _parse_accelerators(
        data=data,
        instances=instances_ref,
        accelerator_catalog=accelerator_catalog,
        err_lines=err_lines,
    )
    _raise_if_errors(label="accelerators", err_lines=err_lines)
    return rtnval


def _parse_accelerators(*, data: Optional[list],
                        instances: List[CloudInstanceSpec],
                        accelerator_catalog: Optional[Any],
                        err_lines: List[str]
                        ) -> List[CloudAcceleratorAssignment]:
    rtnval: List[CloudAcceleratorAssignment] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("accelerators must be a list.")
        return rtnval
    known_instances = {i.name for i in instances}
    for idx, entry in enumerate(raw_list):
        path = f"accelerators[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("instance_name", "accelerators"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        instance_name = entry["instance_name"]
        if len(known_instances) > 0 and instance_name not in known_instances:
            err_lines.append(
                f"{path}.instance_name={instance_name!r} does not reference "
                f"any declared devices[*].name / instances[*].name."
            )
            continue
        specs = _parse_accelerator_specs(
            raw=entry["accelerators"],
            path=f"{path}.accelerators",
            accelerator_catalog=accelerator_catalog,
            err_lines=err_lines,
        )
        assignment = CloudAcceleratorAssignment(
            instance_name=instance_name,
            accelerators=specs,
        )
        rtnval.append(assignment)
    return rtnval


def _parse_accelerator_specs(*, raw: Any, path: str,
                             accelerator_catalog: Optional[Any],
                             err_lines: List[str]
                             ) -> List[CloudAcceleratorSpec]:
    rtnval: List[CloudAcceleratorSpec] = []
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
            required=("kind", "model", "count", "memory_gb"),
            path=item_path,
            err_lines=err_lines,
        ):
            continue
        kind = _validate_enum(
            raw=entry["kind"],
            accepted=SUPPORTED_ACCELERATOR_KINDS,
            path=f"{item_path}.kind",
            err_lines=err_lines,
        )
        if kind is None:
            continue
        interconnect = _validate_enum(
            raw=entry.get("interconnect", "NONE"),
            accepted=SUPPORTED_ACCELERATOR_INTERCONNECTS,
            path=f"{item_path}.interconnect",
            err_lines=err_lines,
        )
        if interconnect is None:
            continue
        count = _validate_int(
            raw=entry["count"], path=f"{item_path}.count",
            err_lines=err_lines, positive=True,
        )
        if count is None:
            continue
        memory_gb = _validate_int(
            raw=entry["memory_gb"], path=f"{item_path}.memory_gb",
            err_lines=err_lines, positive=True,
        )
        if memory_gb is None:
            continue
        model_name = entry["model"]
        if not _accelerator_model_known(
            model_name=model_name,
            accelerator_catalog=accelerator_catalog,
        ):
            err_lines.append(
                f"{item_path}.model={model_name!r} is not present in the "
                f"accelerator catalog."
            )
            continue
        spec = CloudAcceleratorSpec(
            kind=kind,
            model=model_name,
            count=count,
            interconnect=interconnect,
            memory_gb=memory_gb,
        )
        rtnval.append(spec)
    return rtnval


def _accelerator_model_known(*, model_name: str,
                             accelerator_catalog: Optional[Any]) -> bool:
    """
        Reports whether an accelerator neutral name is present in the catalog.

        When no catalog is supplied the model name is accepted unconditionally,
        deferring catalog enforcement to the caller that owns the catalog.

        :param model_name: The accelerator neutral name to check.
        :param accelerator_catalog: Optional ``CloudAcceleratorCatalog``.

        :returns: ``True`` when the model is known or no catalog was supplied.
    """
    if accelerator_catalog is None:
        rtnval = True
        return rtnval
    known_names = set()
    for catalog_entry in accelerator_catalog.entries():
        known_names.add(catalog_entry.neutral_name)
    rtnval = model_name in known_names
    return rtnval


def load_cloud_shared_filesystems_block(*, data: Optional[list] = None,
                                        instances: Optional[List[CloudInstanceSpec]] = None
                                        ) -> List[CloudSharedFilesystem]:
    """
        Parses and validates the ``shared_filesystems:`` block.

        Each entry must declare either ``size_tb`` (provision mode) or
        ``existing_id`` (attach mode) -- the attach-or-provision discriminator.

        :param data: The raw list value of the ``shared_filesystems:`` key.
        :param instances: Already-parsed instances used to validate
            ``mount_targets[*].target_instance`` cross-references.

        :returns: List of parsed ``CloudSharedFilesystem`` instances.
        :raises: ConfigurationError on validation failure.
    """
    err_lines: List[str] = []
    instances_ref = instances if instances is not None else []
    rtnval = _parse_shared_filesystems(
        data=data, instances=instances_ref, err_lines=err_lines
    )
    _raise_if_errors(label="shared_filesystems", err_lines=err_lines)
    return rtnval


def _parse_shared_filesystems(*, data: Optional[list],
                              instances: List[CloudInstanceSpec],
                              err_lines: List[str]
                              ) -> List[CloudSharedFilesystem]:
    rtnval: List[CloudSharedFilesystem] = []
    raw_list = data if data is not None else []
    if not isinstance(raw_list, list):
        err_lines.append("shared_filesystems must be a list.")
        return rtnval
    known_instances = {i.name for i in instances}
    for idx, entry in enumerate(raw_list):
        path = f"shared_filesystems[{idx}]"
        if not _require_mapping(entry=entry, path=path, err_lines=err_lines):
            continue
        if not _require_keys(
            entry=entry,
            required=("name", "kind"),
            path=path,
            err_lines=err_lines,
        ):
            continue
        kind = _validate_enum(
            raw=entry["kind"],
            accepted=SUPPORTED_SHARED_FS_KINDS,
            path=f"{path}.kind",
            err_lines=err_lines,
        )
        if kind is None:
            continue
        size_tb = entry.get("size_tb")
        existing_id = entry.get("existing_id")
        if size_tb is None and existing_id is None:
            err_lines.append(
                f"{path} must declare either 'size_tb' (provision) or "
                f"'existing_id' (attach)."
            )
            continue
        size_tb_val = None
        if size_tb is not None:
            size_tb_val = _validate_int(
                raw=size_tb, path=f"{path}.size_tb",
                err_lines=err_lines, positive=True,
            )
            if size_tb_val is None:
                continue
        throughput_val = None
        if entry.get("throughput_gbps") is not None:
            throughput_val = _validate_int(
                raw=entry["throughput_gbps"],
                path=f"{path}.throughput_gbps",
                err_lines=err_lines, positive=True,
            )
            if throughput_val is None:
                continue
        tags_value = _normalise_tags(
            raw=entry.get("tags"), path=f"{path}.tags", err_lines=err_lines
        )
        if tags_value is None:
            continue
        mount_targets = _parse_shared_fs_mount_targets(
            raw=entry.get("mount_targets", []),
            path=f"{path}.mount_targets",
            filesystem_name=entry["name"],
            known_instances=known_instances,
            err_lines=err_lines,
        )
        spec = CloudSharedFilesystem(
            name=entry["name"],
            kind=kind,
            size_tb=size_tb_val,
            throughput_gbps=throughput_val,
            mount_targets=mount_targets,
            existing_id=existing_id,
            tags=tags_value,
        )
        rtnval.append(spec)
    return rtnval


def _parse_shared_fs_mount_targets(*, raw: Any, path: str,
                                   filesystem_name: str,
                                   known_instances: set,
                                   err_lines: List[str]
                                   ) -> List[SharedFsMountSpec]:
    rtnval: List[SharedFsMountSpec] = []
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
            required=("target_instance", "mount_path"),
            path=item_path,
            err_lines=err_lines,
        ):
            continue
        target_instance = entry["target_instance"]
        if len(known_instances) > 0 and target_instance not in known_instances:
            err_lines.append(
                f"{item_path}.target_instance={target_instance!r} does not "
                f"reference any declared devices[*].name / instances[*].name."
            )
            continue
        mount = SharedFsMountSpec(
            filesystem_name=entry.get("filesystem_name", filesystem_name),
            target_instance=target_instance,
            mount_path=entry["mount_path"],
            mount_options=list(entry.get("mount_options", [])),
        )
        rtnval.append(mount)
    return rtnval


def load_cloud_venues_block(*, data: Optional[dict] = None
                            ) -> List[CloudVenueOverrides]:
    """
        Parses the ``venues:`` block of per-venue overrides.

        The override payload is forwarded verbatim — this loader only
        captures the per-venue dict mapping.

        :param data: The raw ``venues:`` mapping.

        :returns: List of ``CloudVenueOverrides``.
        :raises: ConfigurationError when the block is not a mapping.
    """
    err_lines: List[str] = []
    rtnval: List[CloudVenueOverrides] = []
    raw = data if data is not None else {}
    if not isinstance(raw, dict):
        err_lines.append("venues must be a mapping of venue-name -> overrides.")
        _raise_if_errors(label="venues", err_lines=err_lines)
        return rtnval
    for venue_name, overrides in raw.items():
        if not isinstance(overrides, dict):
            err_lines.append(
                f"venues.{venue_name} must be a mapping."
            )
            continue
        spec = CloudVenueOverrides(
            name=venue_name,
            overrides=dict(overrides),
        )
        rtnval.append(spec)
    _raise_if_errors(label="venues", err_lines=err_lines)
    return rtnval


def warn_unknown_venue_override(*, venue_name: str,
                                override_key: str) -> None:
    """
        Logs a warning when a venue plugin reports an unknown override key.

        Per Requirement 7.3, an unknown override key is forward-compatible and
        therefore a warning rather than an error -- the venue plugin owns its
        own override schema and may not recognise newer keys.

        :param venue_name: Identifier of the venue that reported the override.
        :param override_key: The override key the plugin did not recognise.
    """
    warn_lines = [
        "Venue plugin reported an unknown override key.",
        f"VENUE: {venue_name}",
        f"OVERRIDE KEY: {override_key}",
        "Overrides are forward-compatible; the key was left unchanged.",
    ]
    warn_msg = os.linesep.join(warn_lines)
    logger.warning(warn_msg)
    return


def _raise_if_errors(*, label: str, err_lines: List[str]) -> None:
    """
        Raises a ``ConfigurationError`` aggregating every accumulated error.

        :param label: The block label used in the error header.
        :param err_lines: Accumulated error lines.

        :raises: ConfigurationError when ``err_lines`` is non-empty.
    """
    if len(err_lines) == 0:
        return
    msg_lines = [f"cloud-provisioning-config-schema validation failed in {label}:"]
    for line in err_lines:
        msg_lines.append("  - " + line)
    err_msg = os.linesep.join(msg_lines)
    raise ConfigurationError(err_msg)


# ---------------------------------------------------------------------------
# Top-level orchestrator.
# ---------------------------------------------------------------------------

def load_cloud_provisioning_block(*, data: Optional[dict] = None,
                                  vpn_block: Optional[VPNBlock] = None,
                                  credential_lookup: Optional[CredentialLookup] = None,
                                  accelerator_catalog: Optional[Any] = None
                                  ) -> CloudProvisioningBlock:
    """
        Parses and validates the full cloud-provisioning portion of a config
        dict in a single pass, returning a typed aggregate.

        :param data: The parsed configuration dict (the same shape returned
            by ``ConfigurationLoader.load_configuration_from_file``).
        :param vpn_block: Optional already-parsed ``VPNBlock`` used for
            cross-reference validation of ``instances[*].vpn_join``.
        :param credential_lookup: Optional callable resolving
            ``vpn_join.control_plane_credential`` identifiers.
        :param accelerator_catalog: Optional ``CloudAcceleratorCatalog`` used
            to validate ``accelerators[*].accelerators[*].model`` neutral
            names.

        :returns: A typed ``CloudProvisioningBlock``.
        :raises: ConfigurationError when any block fails validation.
    """
    payload = data if data is not None else {}
    networks = load_cloud_networks_block(data=payload.get("networks"))
    subnets = load_cloud_subnets_block(
        data=payload.get("subnets"), networks=networks
    )
    security_groups = load_cloud_security_groups_block(
        data=payload.get("security_groups"), networks=networks
    )
    keypairs = load_cloud_keypairs_block(data=payload.get("keypairs"))
    images = load_cloud_images_block(data=payload.get("images"))
    instances = load_cloud_instances_block(
        data=payload.get("instances"),
        images=images,
        subnets=subnets,
        security_groups=security_groups,
        keypairs=keypairs,
        vpn_block=vpn_block,
        credential_lookup=credential_lookup,
    )
    volumes = load_cloud_volumes_block(data=payload.get("volumes"))
    buckets = load_cloud_buckets_block(data=payload.get("buckets"))
    load_balancers = load_cloud_load_balancers_block(
        data=payload.get("load_balancers"),
        subnets=subnets,
        instances=instances,
    )
    dns_records = load_cloud_dns_records_block(data=payload.get("dns_records"))
    accelerators = load_cloud_accelerators_block(
        data=payload.get("accelerators"),
        instances=instances,
        accelerator_catalog=accelerator_catalog,
    )
    shared_filesystems = load_cloud_shared_filesystems_block(
        data=payload.get("shared_filesystems"),
        instances=instances,
    )
    venues = load_cloud_venues_block(data=payload.get("venues"))

    rtnval = CloudProvisioningBlock(
        networks=networks,
        subnets=subnets,
        security_groups=security_groups,
        keypairs=keypairs,
        images=images,
        instances=instances,
        volumes=volumes,
        buckets=buckets,
        load_balancers=load_balancers,
        dns_records=dns_records,
        accelerators=accelerators,
        shared_filesystems=shared_filesystems,
        venues=venues,
    )
    return rtnval


# ---------------------------------------------------------------------------
# Dump helpers (round-trip).
# ---------------------------------------------------------------------------

def dump_cloud_networks_block(*, networks: List[CloudNetworkSpec]) -> list:
    """
        Renders the ``networks:`` block back to a list of dicts.

        :param networks: List of ``CloudNetworkSpec``.

        :returns: List shaped like the original YAML.
    """
    rtnval: list = []
    for net in networks:
        entry = {
            "name": net.name,
            "cidr": net.cidr,
            "region": net.region,
            "tags": list(net.tags),
        }
        rtnval.append(entry)
    return rtnval


def dump_cloud_subnets_block(*, subnets: List[CloudSubnetSpec]) -> list:
    """
        Renders the ``subnets:`` block back to a list of dicts.

        :param subnets: List of ``CloudSubnetSpec``.

        :returns: List shaped like the original YAML.
    """
    rtnval: list = []
    for sub in subnets:
        entry = {
            "name": sub.name,
            "network": sub.network,
            "cidr": sub.cidr,
            "zone": sub.zone,
            "public": sub.public,
        }
        rtnval.append(entry)
    return rtnval

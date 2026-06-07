"""
.. module:: test_schema_canonical_types
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Regression tests asserting the config-schema fragments import
        and use the REAL upstream types (hard imports) rather than the
        previous structurally divergent local fallback stand-ins.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []


import sys

from pathlib import Path


# Ensure the local package sources and virtual environment dependencies are available
REPO_ROOT = Path(__file__).resolve().parents[6]
PACKAGE_PATHS = [
    REPO_ROOT / "source" / "packages",
    REPO_ROOT / ".venv" / "src",
    REPO_ROOT / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
]
for pkg_path in PACKAGE_PATHS:
    if pkg_path.exists():
        sys.path.insert(0, str(pkg_path))


def test_vpn_schema_addressplane_is_canonical() -> None:
    """
        ``vpnconfigschema.AddressPlane`` must be the canonical
        ``automojo.interfaces.addressplane.AddressPlane`` type.
    """
    from automojo.configuration.schemas import vpnconfigschema
    from automojo.interfaces.addressplane import AddressPlane

    assert vpnconfigschema.AddressPlane is AddressPlane
    return


def test_vpn_schema_overlayprofile_is_canonical() -> None:
    """
        ``vpnconfigschema.VPNOverlayProfile`` must be the canonical
        ``automojo.networking`` type.
    """
    from automojo.configuration.schemas import vpnconfigschema
    from automojo.networking.vpnoverlayprofile import VPNOverlayProfile

    assert vpnconfigschema.VPNOverlayProfile is VPNOverlayProfile
    return


def test_cloud_schema_vpnjoinspec_is_canonical() -> None:
    """
        ``cloudprovisioningconfigschema.VPNJoinSpec`` must be the
        canonical ``automojo.provisioning`` type that REQUIRES
        ``hostname_template`` (the fallback made it optional).
    """
    from automojo.configuration.schemas import cloudprovisioningconfigschema
    from automojo.provisioning.model.vpn.vpnjoinspec import VPNJoinSpec

    assert cloudprovisioningconfigschema.VPNJoinSpec is VPNJoinSpec
    return


def test_workload_schema_venuekind_is_canonical_enum() -> None:
    """
        ``workloadprovisioningconfigschema.WorkloadVenueKind`` must be
        the canonical ENUM (the fallback was a divergent string tuple).
    """
    from automojo.configuration.schemas import workloadprovisioningconfigschema
    from automojo.provisioning.model.workload.workloadvenuekind import (
        WorkloadVenueKind,
    )

    assert workloadprovisioningconfigschema.WorkloadVenueKind is WorkloadVenueKind
    kinds = workloadprovisioningconfigschema.WORKLOAD_VENUE_KINDS
    assert "kubernetes" in kinds
    return


def test_cloud_schema_canonical_cloud_types() -> None:
    """
        The cloud-model types must be the canonical ``automojo``
        provisioning types, not local fallbacks.
    """
    from automojo.configuration.schemas import cloudprovisioningconfigschema
    from automojo.provisioning.model.cloud.cloudacceleratorspec import (
        CloudAcceleratorSpec,
    )
    from automojo.provisioning.model.cloud.cloudsharedfilesystem import (
        CloudSharedFilesystem,
    )

    assert cloudprovisioningconfigschema.CloudAcceleratorSpec is CloudAcceleratorSpec
    assert cloudprovisioningconfigschema.CloudSharedFilesystem is CloudSharedFilesystem
    return

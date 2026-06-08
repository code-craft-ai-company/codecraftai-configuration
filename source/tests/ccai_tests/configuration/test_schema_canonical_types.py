"""
.. module:: test_schema_canonical_types
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Regression tests asserting the config-schema fragments import
        and use the REAL upstream types (hard imports) rather than the
        previous structurally divergent local fallback stand-ins.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import sys
import unittest

from pathlib import Path


# Ensure the local package sources and virtual environment dependencies are available
REPO_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_PATHS = [
    REPO_ROOT / "source" / "packages",
    REPO_ROOT / ".venv" / "src",
    REPO_ROOT / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
]
for pkg_path in PACKAGE_PATHS:
    if pkg_path.exists():
        sys.path.insert(0, str(pkg_path))


class TestSchemaCanonicalTypes(unittest.TestCase):
    """
        Asserts the schema fragments resolve the canonical upstream types.

        Prior to the audit fix, three schema imports pointed at wrong module
        paths so the ``try/except ImportError`` fallback ran unconditionally,
        substituting structurally divergent stand-ins. These tests fail loudly
        if the regression returns.
    """

    def test_vpn_schema_addressplane_is_canonical(self) -> None:
        """
            ``vpnconfigschema.AddressPlane`` must be the canonical
            ``ccai.interfaces.addressplane.AddressPlane`` type.
        """
        from ccai.configuration.schemas import vpnconfigschema
        from ccai.interfaces.addressplane import AddressPlane

        self.assertIs(vpnconfigschema.AddressPlane, AddressPlane)
        return

    def test_vpn_schema_overlayprofile_is_canonical(self) -> None:
        """
            ``vpnconfigschema.VPNOverlayProfile`` must be the canonical
            ``ccai.networking`` type.
        """
        from ccai.configuration.schemas import vpnconfigschema
        from ccai.networking.vpnoverlayprofile import VPNOverlayProfile

        self.assertIs(vpnconfigschema.VPNOverlayProfile, VPNOverlayProfile)
        return

    def test_cloud_schema_vpnjoinspec_is_canonical(self) -> None:
        """
            ``cloudprovisioningconfigschema.VPNJoinSpec`` must be the
            canonical ``ccai.provisioning`` type that REQUIRES
            ``hostname_template`` (the fallback made it optional).
        """
        from ccai.configuration.schemas import cloudprovisioningconfigschema
        from ccai.provisioning.model.vpn.vpnjoinspec import VPNJoinSpec

        self.assertIs(cloudprovisioningconfigschema.VPNJoinSpec, VPNJoinSpec)
        return

    def test_workload_schema_venuekind_is_canonical_enum(self) -> None:
        """
            ``workloadprovisioningconfigschema.WorkloadVenueKind`` must be
            the canonical ENUM (the fallback was a divergent string tuple).
        """
        from ccai.configuration.schemas import workloadprovisioningconfigschema
        from ccai.provisioning.model.workload.workloadvenuekind import (
            WorkloadVenueKind,
        )

        self.assertIs(
            workloadprovisioningconfigschema.WorkloadVenueKind,
            WorkloadVenueKind,
        )
        kinds = workloadprovisioningconfigschema.WORKLOAD_VENUE_KINDS
        self.assertIn("kubernetes", kinds)
        return

    def test_cloud_schema_canonical_cloud_types(self) -> None:
        """
            The cloud-model types must be the canonical ``ccai``
            provisioning types, not local fallbacks.
        """
        from ccai.configuration.schemas import cloudprovisioningconfigschema
        from ccai.provisioning.model.cloud.cloudacceleratorspec import (
            CloudAcceleratorSpec,
        )
        from ccai.provisioning.model.cloud.cloudsharedfilesystem import (
            CloudSharedFilesystem,
        )

        self.assertIs(
            cloudprovisioningconfigschema.CloudAcceleratorSpec,
            CloudAcceleratorSpec,
        )
        self.assertIs(
            cloudprovisioningconfigschema.CloudSharedFilesystem,
            CloudSharedFilesystem,
        )
        return


if __name__ == "__main__":
    unittest.main()

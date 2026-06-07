"""
.. module:: configurationloader
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that implements configuration loading from various sources.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Dict, List, Optional, Tuple

import os
import json
import yaml
import base64

from cryptography.fernet import Fernet

from ccai.errors.exceptions import ConfigurationError, SemanticError

from ccai.configuration.sources.configurationsourcebase import ConfigurationSourceBase
from ccai.configuration.sources.couchdbsource import CouchDBSource
from ccai.configuration.sources.directorysource import DirectorySource
from ccai.configuration.sources.mongodbsource import MongoDBSource
from ccai.configuration.sources.httpsource import HttpSource
from ccai.configuration.configurationformat import ConfigurationFormat
from ccai.configuration.cryptography import generate_fernet_key, decrypt_content
from ccai.configuration.schemas.vpnconfigschema import VPNBlock, load_vpn_block
from ccai.configuration.schemas.cloudprovisioningconfigschema import (
    load_cloud_accelerators_block,
    load_cloud_buckets_block,
    load_cloud_dns_records_block,
    load_cloud_images_block,
    load_cloud_instances_block,
    load_cloud_keypairs_block,
    load_cloud_load_balancers_block,
    load_cloud_networks_block,
    load_cloud_security_groups_block,
    load_cloud_shared_filesystems_block,
    load_cloud_subnets_block,
    load_cloud_volumes_block,
)
from ccai.configuration.schemas.workloadprovisioningconfigschema import (
    load_workload_clusters_block,
    load_workload_jobs_block,
    load_workload_services_block,
    load_workload_venues_block,
)


# Registry of top-level configuration keys mapped to (loader_callable, label).
# Other ccai packages compose into this registry rather than carrying
# their own copy of the schema -- see §8 commitment #4 in
# IMPLEMENTATION-PLAN.md ("one spec, two read paths: typed object + dict").
TOP_LEVEL_SCHEMA_LOADERS = {
    "vpn": load_vpn_block,
    "networks": load_cloud_networks_block,
    "subnets": load_cloud_subnets_block,
    "security_groups": load_cloud_security_groups_block,
    "keypairs": load_cloud_keypairs_block,
    "images": load_cloud_images_block,
    "instances": load_cloud_instances_block,
    "volumes": load_cloud_volumes_block,
    "buckets": load_cloud_buckets_block,
    "load_balancers": load_cloud_load_balancers_block,
    "dns_records": load_cloud_dns_records_block,
    "accelerators": load_cloud_accelerators_block,
    "shared_filesystems": load_cloud_shared_filesystems_block,
    "workload_venues": load_workload_venues_block,
    "workload_clusters": load_workload_clusters_block,
    "workload_jobs": load_workload_jobs_block,
    "workload_services": load_workload_services_block,
}


class ConfigurationLoader:
    """
        The :class:`ConfigurationLoader` provides configuration loading from multiple references and
        source classes.
    """

    def __init__(self, source_uris: List[str], credentials: Optional[Dict[str, Tuple[str, str]]] = None, verify_certificate: bool = True):
        """
            Constructs a new :class:`ConfigurationLoader`.

            :param source_uris: List of configuration source URIs.
            :param credentials: Optional mapping of host names to credentials.
            :param verify_certificate: ``True`` to verify HTTPS certificates.
        """
        self._source_uris = [uri.strip() for uri in source_uris]
        self._credentials = credentials
        self._verify_certificate = verify_certificate

        self._sources: List[ConfigurationSourceBase] = []
        self._initialize()
        return


    @property
    def source_uris(self) -> List[str]:
        """
            List of source URIs to search for configurations.
        """
        return self._source_uris


    @property
    def sources(self) -> List[ConfigurationSourceBase]:
        """
            List of parsed configuration source objects.
        """
        return self._sources


    def load_configuration_from_file(self, config_file: str, key: Optional[str] = None, keyphrase: Optional[str] = None) -> dict:
        """
            Loads a configuration directly from a file.

            :param config_name: The path to the configuration file to load.
            :param key: An optional key to use for encrypted configurations.
            :param keyphrase: An optional phrase to use for generating the decryption key.

            :returns: A deep dictionary containing the configuration that was loaded.
        """

        if key is not None and keyphrase is not None:
            errmsg = "The 'load_configuration' method should be called with either 'key' or 'keyphrase' but not both."
            raise SemanticError(errmsg)

        if keyphrase is not None:
            key = generate_fernet_key(keyphrase)

        config_info = None
        config_format = None

        _, fileext = os.path.splitext(config_file)

        if fileext in [".yaml", ".yml"]:
            with open(config_file, 'r') as cf:
                config_info = yaml.safe_load(cf)
        elif fileext == ".json":
            with open(config_file, 'r') as cf:
                config_info = json.load(cf)
        else:
            errmsg = f"Un-supported configuration file extension '{fileext}' for file '{config_file}'."
            raise ConfigurationError(errmsg)

        if "encrypted_content" in config_info:
            if "format" in config_info:
                config_format = config_info["format"]

            if key is None:
                errmsg = "Encrypted configuration content found but no key or keyphrase was provided."
                raise ConfigurationError(errmsg)

            decryptor = Fernet(key)
            
            encrypted_content = base64.b64decode(config_info["encrypted_content"])
            
            plain_content = decryptor.decrypt(encrypted_content).decode('utf-8')

            if config_format == ConfigurationFormat.YAML:
                config_info = yaml.safe_load(plain_content)
            elif config_format == ConfigurationFormat.JSON:
                config_info = json.loads(plain_content)
            else:
                errmsg = "UnExpected error parsing decrypted configuration content.  Un-supported format."
                raise ConfigurationError(errmsg)

        return config_info


    def load_configuration_by_name(self, config_name: str, key: Optional[str] = None, keyphrase: Optional[str] = None) -> Tuple[str, dict]:
        """
            Searches a list of sources to locate a configuration by name and then loads the configuration.

            :param config_name: The name of the configuration to load.
            :param key: An optional key to use for encrypted configurations.
            :param keyphrase: An optional phrase to use for generating the decryption key.

            :returns: A tuple with the uri used to locate the configuration and the configuration found
        """
        
        if key is not None and keyphrase is not None:
            errmsg = "The 'load_configuration' method should be called with either 'key' or 'keyphrase' but not both."
            raise SemanticError(errmsg)

        if keyphrase is not None:
            key = generate_fernet_key(keyphrase)

        config_info = None
        config_format = None
        config_uri = None

        for src in self._sources:
            config_format, config_info = src.try_load_configuration(config_name, self._credentials)
            if config_info is not None:
                config_uri = f"{src.uri}/{config_name}"
                break

        if config_info is None:
            errmsg_list = [
                f"Unable to locate configuration name='{config_name}'",
                "CHECKED SOURCES:"
            ]

            for uri in self.source_uris:
                errmsg_list.append(f"    {uri}")

            errmsg = os.linesep.join(errmsg_list)
            raise ConfigurationError(errmsg)

        if "encrypted_content" in config_info:

            if "format" in config_info:
                config_format = config_info["format"]

            if key is None:
                errmsg = "Encrypted configuration content found but no key or keyphrase was provided."
                raise ConfigurationError(errmsg)

            encrypted_content = config_info["encrypted_content"]

            plain_content = decrypt_content(key, encrypted_content)

            if config_format == ConfigurationFormat.YAML:
                config_info = yaml.safe_load(plain_content)
            elif config_format == ConfigurationFormat.JSON:
                config_info = json.loads(plain_content)
            else:
                errmsg = "UnExpected error parsing decrypted configuration content.  Un-supported format."
                raise ConfigurationError(errmsg)

        return config_uri, config_info


    def load_vpn_block_from_config(self, config_info: dict) -> VPNBlock:
        """
            Extracts and validates the top-level ``vpn:`` block from an
            already-loaded configuration dict.

            :param config_info: A parsed configuration dict (the same shape
                returned by ``load_configuration_from_file`` or
                ``load_configuration_by_name``).

            :returns: A typed :class:`VPNBlock`. When the dict has no
                ``vpn:`` key, the returned block has
                ``default_plane=AddressPlane.PUBLIC`` and an empty
                providers list.
            :raises: ConfigurationError when the ``vpn:`` block is present
                but malformed.
        """
        vpn_data = None
        if config_info is not None and "vpn" in config_info:
            vpn_data = config_info["vpn"]

        rtnval = load_vpn_block(data=vpn_data)
        return rtnval


    def _initialize(self):

        for uri in self._source_uris:
            if uri.startswith(CouchDBSource.scheme):
                src = CouchDBSource.parse(uri)

                if src is None:
                    errmsg = f"CouchDBSource encountered an error parsing configuration source uri='{uri}'"
                    raise ConfigurationError(errmsg)

                self._sources.append(src)

            elif uri.startswith(MongoDBSource.scheme):
                src = MongoDBSource.parse(uri, verify_certificate=self._verify_certificate)
                
                if src is None:
                    errmsg = f"MongoDBSource encountered an error parsing configuration source uri='{uri}'"
                    raise ConfigurationError(errmsg)
                
                self._sources.append(src)

            elif uri.startswith(HttpSource.scheme) or uri.startswith(HttpSource.secure_scheme):
                src = HttpSource.parse(uri)
                
                if src is None:
                    errmsg = f"HttpSource encountered an error parsing configuration source uri='{uri}'"
                    raise ConfigurationError(errmsg)
                
                self._sources.append(src)

            else:
                src = DirectorySource.parse(uri)
                
                if src is None:
                    errmsg = f"DirectorySource encountered an error parsing configuration source uri='{uri}'"
                    raise ConfigurationError(errmsg)

                self._sources.append(src)

        return
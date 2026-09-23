"""
.. module:: configurationmaps
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains functions for searching for and loading different types of
               automation runtime configuration maps.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Dict, Optional, Tuple

import os

from collections import OrderedDict

from ccai.thisapp.thisapplication import ThisApplication
from ccai.thisapp.wellknown import ThisApplicationSingleton

from ccai.configuration.configurationvariables import (
    ConfigVariables,
    CONFIGURATION_MAPS
)

from ccai.configuration.configurationvariables import ConfigVariablesDesc
from ccai.configuration.configurationloader import ConfigurationLoader


CREDENTIALS_TABLE = None
DATAPROFILES_TABLE = None
LANDSCAPE_TABLE = None
RUNTIME_TABLE = None
TOPOLOGY_TABLE = None


def resolve_configuration_maps(
        use_credentials: Optional[bool]=None,
        use_dataprofiles: Optional[bool]=None,
        use_landscape: Optional[bool]=None,
        use_runtime: Optional[bool]=None,
        use_topology: Optional[bool]=None,
        keyphrase: Optional[str]=None,
        credentials: Optional[Dict[str, Tuple[str, str]]] = None):


    this_app = ThisApplicationSingleton()


    if use_credentials is None:
        use_credentials = ConfigVariables.AM_CONFIG_USE_CREDENTIALS
    else:
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_CREDENTIALS, use_credentials)

    if use_dataprofiles is None:
        use_dataprofiles = ConfigVariables.AM_CONFIG_USE_DATAPROFILES
    else:
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_DATAPROFILES, use_dataprofiles)
    
    if use_landscape is None:
        use_landscape = ConfigVariables.AM_CONFIG_USE_LANDSCAPE
    else:
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_LANDSCAPE, use_landscape)
    
    if use_runtime is None:
        use_runtime = ConfigVariables.AM_CONFIG_USE_RUNTIME
    else:
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_RUNTIME, use_runtime)

    if use_topology is None:
        use_topology = ConfigVariables.AM_CONFIG_USE_TOPOLOGY
    else:
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_TOPOLOGY, use_topology)


    if keyphrase is None:
        keyphrase = ConfigVariables.AM_CONFIG_PASS_PHRASE
    else:
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_PASS_PHRASE, keyphrase)


    if use_credentials:
        resolve_credentials_configuration(this_app, keyphrase=keyphrase, credentials=credentials)

    if use_dataprofiles:
        resolve_dataprofiles_configuration(this_app, keyphrase=keyphrase, credentials=credentials)

    if use_landscape:
        resolve_landscape_configuration(this_app, keyphrase=keyphrase, credentials=credentials)

    if use_runtime:
        resolve_runtime_configuration(this_app, keyphrase=keyphrase, credentials=credentials)

    if use_topology:
        resolve_topology_configuration(this_app, keyphrase=keyphrase, credentials=credentials)

    return


def resolve_credentials_configuration(this_app: ThisApplication, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global CREDENTIALS_TABLE

    CREDENTIALS_TABLE = OrderedDict()
 
    credential_uris = []

    config_directory =  this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_DIRECTORY)

    config_names = ConfigVariables.AM_CONFIG_CREDENTIAL_NAMES
    config_files = ConfigVariables.AM_CONFIG_CREDENTIAL_FILES
    config_sources = ConfigVariables.AM_CONFIG_CREDENTIAL_SOURCES

    # We were told to use credentials but we dont have any config_names or config_files, that means to use the default config.
    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        config_names = ["default-credentials"]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_NAMES, config_names)

    if config_names is not None and len(config_names) > 0 and (config_sources is None or len(config_sources) == 0):
        config_sources = [
            os.path.join(config_directory, "credentials")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_SOURCES, config_sources)

    if config_names is not None and len(config_names) > 0:
        config_loader = ConfigurationLoader(config_sources, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            CREDENTIALS_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.CREDENTIAL_CONFIGURATION_MAP.maps.insert(0, config_info)

        credential_uris = [ cfguri for cfguri in  CREDENTIALS_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.CREDENTIAL_CONFIGURATION_MAP.maps.insert(0, config_info)

    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_URIS, credential_uris)

    return


def resolve_dataprofiles_configuration(this_app: ThisApplication, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global DATAPROFILES_TABLE

    DATAPROFILES_TABLE = OrderedDict()

    dataprofiles_uris = []

    config_directory =  this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_DIRECTORY)

    config_names = ConfigVariables.AM_CONFIG_DATAPROFILE_NAMES
    config_files = ConfigVariables.AM_CONFIG_DATAPROFILE_FILES
    config_sources = ConfigVariables.AM_CONFIG_DATAPROFILE_SOURCES

    # We were told to use credentials but we dont have any config_names or config_files, that means to use the default config.
    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        config_names = ["default-dataprofiles"]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_NAMES, config_names)

    if config_names is not None and len(config_names) > 0 and (config_sources is None or len(config_sources) == 0):
        config_sources = [
            os.path.join(config_directory, "dataprofiles")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_SOURCES, config_sources)

    if config_names is not None and len(config_names) > 0:

        config_loader = ConfigurationLoader(config_sources, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            DATAPROFILES_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.DATAPROFILE_CONFIGURATION_MAP.maps.insert(0, config_info)

        dataprofiles_uris = [ cfguri for cfguri in  DATAPROFILES_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.DATAPROFILE_CONFIGURATION_MAP.maps.insert(0, config_info)

    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_URIS, dataprofiles_uris)

    return


def resolve_landscape_configuration(this_app: ThisApplication, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global LANDSCAPE_TABLE

    LANDSCAPE_TABLE = OrderedDict()

    landscape_uris = []

    config_directory =  this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_DIRECTORY)

    config_names = ConfigVariables.AM_CONFIG_LANDSCAPE_NAMES
    config_files = ConfigVariables.AM_CONFIG_LANDSCAPE_FILES
    config_sources = ConfigVariables.AM_CONFIG_LANDSCAPE_SOURCES

    # We were told to use credentials but we dont have any config_names or config_files, that means to use the default config.
    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        config_names = ["default-landscape"]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_NAMES, config_names)

    if config_names is not None and len(config_names) > 0 and (config_sources is None or len(config_sources) == 0):
        config_sources = [
            os.path.join(config_directory, "landscapes")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_SOURCES, config_sources)

    if config_names is not None and len(config_names) > 0:

        config_loader = ConfigurationLoader(config_sources, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            LANDSCAPE_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.LANDSCAPE_CONFIGURATION_MAP.maps.insert(0, config_info)

        landscape_uris = [ cfguri for cfguri in  LANDSCAPE_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.LANDSCAPE_CONFIGURATION_MAP.maps.insert(0, config_info)

    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_URIS, landscape_uris)

    return


def resolve_runtime_configuration(this_app: ThisApplication, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global RUNTIME_TABLE

    RUNTIME_TABLE = OrderedDict()

    runtime_uris = []

    config_directory =  this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_DIRECTORY)

    config_names = ConfigVariables.AM_CONFIG_RUNTIME_NAMES
    config_files = ConfigVariables.AM_CONFIG_RUNTIME_FILES
    config_sources = ConfigVariables.AM_CONFIG_RUNTIME_SOURCES

    # We were told to use credentials but we dont have any config_names or config_files, that means to use the default config.
    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        config_names = ["default-runtime"]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_RUNTIME_NAMES, config_names)

    if config_names is not None and len(config_names) > 0 and (config_sources is None or len(config_sources) == 0):
        config_sources = [
            os.path.join(config_directory, "runtimes")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_RUNTIME_SOURCES, config_sources)

    if config_names is not None and len(config_names) > 0:

        config_loader = ConfigurationLoader(config_sources, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            RUNTIME_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.RUNTIME_CONFIGURATION_MAP.maps.insert(0, config_info)

        runtime_uris = [ cfguri for cfguri in  RUNTIME_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.RUNTIME_CONFIGURATION_MAP.maps.insert(0, config_info)

    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_RUNTIME_URIS, runtime_uris)

    return


def resolve_topology_configuration(this_app: ThisApplication, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global TOPOLOGY_TABLE

    TOPOLOGY_TABLE = OrderedDict()

    topology_uris = []

    config_directory =  this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_DIRECTORY)

    config_names = ConfigVariables.AM_CONFIG_TOPOLOGY_NAMES
    config_files = ConfigVariables.AM_CONFIG_TOPOLOGY_FILES
    config_sources = ConfigVariables.AM_CONFIG_TOPOLOGY_SOURCES

    # We were told to use credentials but we dont have any config_names or config_files, that means to use the default config.
    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        config_names = ["default-topology"]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_NAMES, config_names)

    if config_names is not None and len(config_names) > 0 and (config_sources is None or len(config_sources) == 0):
        config_sources = [
            os.path.join(config_directory, "topologies")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_SOURCES, config_sources)

    if config_names is not None and len(config_names) > 0:

        config_loader = ConfigurationLoader(config_sources, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            TOPOLOGY_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.TOPOLOGY_CONFIGURATION_MAP.maps.insert(0, config_info)

        topology_uris = [ cfguri for cfguri in  TOPOLOGY_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.TOPOLOGY_CONFIGURATION_MAP.maps.insert(0, config_info)

    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_URIS, topology_uris)

    #ctx.insert(ContextPaths.CONFIG_TOPOLOGY, CONFIGURATION_MAPS.TOPOLOGY_CONFIGURATION_MAP)
    
    return


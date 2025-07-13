"""
.. module:: configurationmaps
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains functions for searching for and loading different types of
               automation runtime configuration maps.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Dict, Optional, Tuple

import os

from collections import OrderedDict

from automojo.errors.exceptions import SemanticError

from automojo.xmodules.xcollections.context import Context
from automojo.xmodules.xcollections.wellknown import ContextSingleton

from automojo.presence.contextpaths import ContextPaths

from automojo.configuration.configurationvariables import (
    AM_CONFIG_VARNAMES,
    AM_CONFIG_VARIABLES,
    CONFIGURATION_MAPS
)


from automojo.configuration.configurationloader import ConfigurationLoader


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

    if use_credentials is None:
        use_credentials = AM_CONFIG_VARIABLES.AM_CONFIG_USE_CREDENTIALS
    else:
        AM_CONFIG_VARIABLES.AM_CONFIG_USE_CREDENTIALS = use_credentials

    if use_dataprofiles is None:
        use_dataprofiles = AM_CONFIG_VARIABLES.AM_CONFIG_USE_DATAPROFILES
    else:
        AM_CONFIG_VARIABLES.AM_CONFIG_USE_DATAPROFILES = use_dataprofiles

    if use_landscape is None:
        use_landscape = AM_CONFIG_VARIABLES.AM_CONFIG_USE_LANDSCAPE
    else:
        AM_CONFIG_VARIABLES.AM_CONFIG_USE_LANDSCAPE = use_landscape
    
    if use_runtime is None:
        use_runtime = AM_CONFIG_VARIABLES.AM_CONFIG_USE_RUNTIME
    else:
        AM_CONFIG_VARIABLES.AM_CONFIG_USE_RUNTIME = use_runtime
    
    if use_topology is None:
        use_topology = AM_CONFIG_VARIABLES.AM_CONFIG_USE_TOPOLOGY
    else:
        AM_CONFIG_VARIABLES.AM_CONFIG_USE_TOPOLOGY = use_topology

    if AM_CONFIG_VARNAMES.AM_CONFIG_PASS_PHRASE in os.environ:
        AM_CONFIG_VARIABLES.AM_CONFIG_PASS_PHRASE = os.environ[AM_CONFIG_VARNAMES.AM_CONFIG_PASS_PHRASE]

    if keyphrase is not None:
        AM_CONFIG_VARIABLES.AM_CONFIG_PASS_PHRASE = keyphrase
    else:
        keyphrase = AM_CONFIG_VARIABLES.AM_CONFIG_PASS_PHRASE

    ctx = ContextSingleton()

    if use_credentials:
        resolve_credentials_configuration(ctx, keyphrase=keyphrase, credentials=credentials)

    if use_dataprofiles:
        resolve_dataprofiles_configuration(ctx, keyphrase=keyphrase, credentials=credentials)

    if use_landscape:
        resolve_landscape_configuration(ctx, keyphrase=keyphrase, credentials=credentials)

    if use_runtime:
        resolve_runtime_configuration(ctx, keyphrase=keyphrase, credentials=credentials)

    if use_topology:
        resolve_topology_configuration(ctx, keyphrase=keyphrase, credentials=credentials)

    return


def resolve_credentials_configuration(ctx: Context, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global CREDENTIALS_TABLE

    CREDENTIALS_TABLE = OrderedDict()

    AM_CONFIG_VARIABLES.AM_CONFIG_CREDENTIAL_URIS = []
    
    config_names = AM_CONFIG_VARIABLES.AM_CONFIG_CREDENTIAL_NAMES
    config_files = AM_CONFIG_VARIABLES.AM_CONFIG_CREDENTIAL_FILES

    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        AM_CONFIG_VARIABLES.AM_CONFIG_CREDENTIAL_NAMES = ["default-credentials"]
        config_names = AM_CONFIG_VARIABLES.AM_CONFIG_CREDENTIAL_NAMES

    if config_names is not None:
        source_bases = AM_CONFIG_VARIABLES.AM_CONFIG_CREDENTIAL_SOURCES
        if source_bases is None:
            errmsg = "The 'AM_CONFIG_CREDENTIAL_SOURCES' variable should not be None.  Did you call 'resolve_configuration_variables'."
            raise SemanticError(errmsg)

        config_loader = ConfigurationLoader(source_bases, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            CREDENTIALS_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.CREDENTIAL_CONFIGURATION_MAP.maps.insert(0, config_info)

        AM_CONFIG_VARIABLES.AM_CONFIG_CREDENTIAL_URIS = [ cfguri for cfguri in  CREDENTIALS_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.CREDENTIAL_CONFIGURATION_MAP.maps.insert(0, config_info)

    ctx.insert(ContextPaths.CONFIG_CREDENTIAL_URIS, AM_CONFIG_VARIABLES.AM_CONFIG_CREDENTIAL_URIS)

    return


def resolve_dataprofiles_configuration(ctx: Context, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global DATAPROFILES_TABLE

    DATAPROFILES_TABLE = OrderedDict()

    AM_CONFIG_VARIABLES.AM_CONFIG_DATAPROFILE_URIS = []
    
    config_names = AM_CONFIG_VARIABLES.AM_CONFIG_DATAPROFILE_NAMES
    config_files = AM_CONFIG_VARIABLES.AM_CONFIG_DATAPROFILE_FILES

    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        AM_CONFIG_VARIABLES.AM_CONFIG_DATAPROFILE_NAMES = ["default-dataprofiles"]
        config_names = AM_CONFIG_VARIABLES.AM_CONFIG_DATAPROFILE_NAMES

    if config_names is not None:
        source_bases = AM_CONFIG_VARIABLES.AM_CONFIG_DATAPROFILE_SOURCES
        if source_bases is None:
            errmsg = "The 'AM_CONFIG_DATAPROFILE_SOURCES' variable should not be None.  Did you call 'resolve_configuration_variables'."
            raise SemanticError(errmsg)

        config_loader = ConfigurationLoader(source_bases, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            DATAPROFILES_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.DATAPROFILE_CONFIGURATION_MAP.maps.insert(0, config_info)

        AM_CONFIG_VARIABLES.AM_CONFIG_DATAPROFILE_URIS = [ cfguri for cfguri in  CREDENTIALS_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.DATAPROFILE_CONFIGURATION_MAP.maps.insert(0, config_info)

    ctx.insert(ContextPaths.CONFIG_DATAPROFILE_URIS, AM_CONFIG_VARIABLES.AM_CONFIG_DATAPROFILE_URIS)

    return


def resolve_landscape_configuration(ctx: Context, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global LANDSCAPE_TABLE

    LANDSCAPE_TABLE = OrderedDict()

    AM_CONFIG_VARIABLES.AM_CONFIG_LANDSCAPE_URIS = []
    
    config_names = AM_CONFIG_VARIABLES.AM_CONFIG_LANDSCAPE_NAMES
    config_files = AM_CONFIG_VARIABLES.AM_CONFIG_LANDSCAPE_FILES

    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        AM_CONFIG_VARIABLES.AM_CONFIG_LANDSCAPE_NAMES = ["default-landscape"]
        config_names = AM_CONFIG_VARIABLES.AM_CONFIG_LANDSCAPE_NAMES

    if config_names is not None:
        source_bases = AM_CONFIG_VARIABLES.AM_CONFIG_LANDSCAPE_SOURCES
        if source_bases is None:
            errmsg = "The 'AM_CONFIG_LANDSCAPE_SOURCES' variable should not be None.  Did you call 'resolve_configuration_variables'."
            raise SemanticError(errmsg)

        config_loader = ConfigurationLoader(source_bases, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            LANDSCAPE_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.LANDSCAPE_CONFIGURATION_MAP.maps.insert(0, config_info)

        AM_CONFIG_VARIABLES.AM_CONFIG_LANDSCAPE_URIS = [ cfguri for cfguri in  LANDSCAPE_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.LANDSCAPE_CONFIGURATION_MAP.maps.insert(0, config_info)

    ctx.insert(ContextPaths.CONFIG_LANDSCAPE, CONFIGURATION_MAPS.LANDSCAPE_CONFIGURATION_MAP)
    ctx.insert(ContextPaths.CONFIG_LANDSCAPE_URIS, AM_CONFIG_VARIABLES.AM_CONFIG_LANDSCAPE_URIS)

    return


def resolve_runtime_configuration(ctx: Context, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global RUNTIME_TABLE

    RUNTIME_TABLE = OrderedDict()

    AM_CONFIG_VARIABLES.AM_CONFIG_RUNTIME_URIS = []

    config_names = AM_CONFIG_VARIABLES.AM_CONFIG_RUNTIME_NAMES
    config_files = AM_CONFIG_VARIABLES.AM_CONFIG_RUNTIME_FILES

    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        AM_CONFIG_VARIABLES.AM_CONFIG_RUNTIME_NAMES = ["default-runtime"]
        config_names = AM_CONFIG_VARIABLES.AM_CONFIG_RUNTIME_NAMES

    if config_names is not None:
        source_bases = AM_CONFIG_VARIABLES.AM_CONFIG_RUNTIME_SOURCES
        if source_bases is None:
            errmsg = "The 'AM_CONFIG_RUNTIME_SOURCES' variable should not be None.  Did you call 'resolve_configuration_variables'."
            raise SemanticError(errmsg)

        config_loader = ConfigurationLoader(source_bases, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            RUNTIME_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.RUNTIME_CONFIGURATION_MAP.maps.insert(0, config_info)

        AM_CONFIG_VARIABLES.AM_CONFIG_RUNTIME_URIS = [ cfguri for cfguri in  RUNTIME_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.RUNTIME_CONFIGURATION_MAP.maps.insert(0, config_info)

    ctx.insert(ContextPaths.CONFIG_RUNTIME, CONFIGURATION_MAPS.RUNTIME_CONFIGURATION_MAP)
    ctx.insert(ContextPaths.CONFIG_RUNTIME_URIS, AM_CONFIG_VARIABLES.AM_CONFIG_RUNTIME_URIS)

    return


def resolve_topology_configuration(ctx: Context, keyphrase: Optional[str] = None, credentials: Optional[Dict[str, Tuple[str, str]]] = None):

    global TOPOLOGY_TABLE

    TOPOLOGY_TABLE = OrderedDict()

    AM_CONFIG_VARIABLES.AM_CONFIG_TOPOLOGY_URIS = []

    config_names = AM_CONFIG_VARIABLES.AM_CONFIG_TOPOLOGY_NAMES
    config_files = AM_CONFIG_VARIABLES.AM_CONFIG_TOPOLOGY_FILES

    if (config_names is None or len(config_names) == 0) and (config_files is None or len(config_files) == 0):
        AM_CONFIG_VARIABLES.AM_CONFIG_TOPOLOGY_NAMES = ["default-topology"]
        config_names = AM_CONFIG_VARIABLES.AM_CONFIG_TOPOLOGY_NAMES

    if config_names is not None:
        source_bases = AM_CONFIG_VARIABLES.AM_CONFIG_TOPOLOGY_SOURCES
        if source_bases is None:
            errmsg = "The 'AM_CONFIG_TOPOLOGY_SOURCES' variable should not be None.  Did you call 'resolve_configuration_variables'."
            raise SemanticError(errmsg)

        config_loader = ConfigurationLoader(source_bases, credentials=credentials)

        for cname in config_names:
            config_uri, config_info = config_loader.load_configuration_by_name(cname, keyphrase=keyphrase)
            TOPOLOGY_TABLE[config_uri] = config_info
            CONFIGURATION_MAPS.TOPOLOGY_CONFIGURATION_MAP.maps.insert(0, config_info)

        AM_CONFIG_VARIABLES.AM_CONFIG_TOPOLOGY_URIS = [ cfguri for cfguri in  TOPOLOGY_TABLE.keys() ]

    if config_files is not None:
        config_loader = ConfigurationLoader([], credentials=credentials)
        for cfile in config_files:
            config_info = config_loader.load_configuration_from_file(cfile, keyphrase=keyphrase)
            CONFIGURATION_MAPS.TOPOLOGY_CONFIGURATION_MAP.maps.insert(0, config_info)

    ctx.insert(ContextPaths.CONFIG_TOPOLOGY, CONFIGURATION_MAPS.TOPOLOGY_CONFIGURATION_MAP)
    ctx.insert(ContextPaths.CONFIG_TOPOLOGY_URIS, AM_CONFIG_VARIABLES.AM_CONFIG_TOPOLOGY_URIS)

    return


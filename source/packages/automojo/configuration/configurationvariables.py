"""
.. module:: varnames
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains an enumeration of environment variable names
               that are used by the configuration code.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import os


from automojo.xmodules.xcollections.mergemap import MergeMap
from automojo.xmodules.xconvert import parse_bool

from automojo.presence.wellknown import ContextSingleton, ThisApplicationSingleton
from automojo.presence.contextpaths import ContextPaths
from automojo.presence.appvarreader import AppVarReader

from automojo.presence.presencevariables import (
    PresenceVariables,
    resolve_presence_variables
)

from automojo.configuration.constants import ConfigVariableDesc

from automojo.configuration.configurationsettings import ConfigurationDefaults

class CONFIGURATION_MAPS:
    CREDENTIAL_CONFIGURATION_MAP = MergeMap()
    DATAPROFILE_CONFIGURATION_MAP = MergeMap()
    LANDSCAPE_CONFIGURATION_MAP = MergeMap()
    RUNTIME_CONFIGURATION_MAP = MergeMap(ConfigurationDefaults.DEFAULT_CONFIGURATION)
    TOPOLOGY_CONFIGURATION_MAP = MergeMap()



class ConfigurationVariables(PresenceVariables):

    AM_CONFIG_REQUIRE_CREDENTIALS = AppVarReader(ConfigVariableDesc.AM_CONFIG_REQUIRE_CREDENTIALS)
    AM_CONFIG_REQUIRE_DATAPROFILES = AppVarReader(ConfigVariableDesc.AM_CONFIG_REQUIRE_DATAPROFILES)
    AM_CONFIG_REQUIRE_LANDSCAPE = AppVarReader(ConfigVariableDesc.AM_CONFIG_REQUIRE_LANDSCAPE)
    AM_CONFIG_REQUIRE_RUNTIME = AppVarReader(ConfigVariableDesc.AM_CONFIG_REQUIRE_RUNTIME)
    AM_CONFIG_REQUIRE_TOPOLOGY = AppVarReader(ConfigVariableDesc.AM_CONFIG_REQUIRE_TOPOLOGY)

    AM_CONFIG_STORAGE_URI = AppVarReader(ConfigVariableDesc.AM_CONFIG_STORAGE_URI)

    AM_CONFIG_USE_CREDENTIALS = AppVarReader(ConfigVariableDesc.AM_CONFIG_USE_CREDENTIALS)
    AM_CONFIG_USE_DATAPROFILES = AppVarReader(ConfigVariableDesc.AM_CONFIG_USE_DATAPROFILES)
    AM_CONFIG_USE_LANDSCAPE = AppVarReader(ConfigVariableDesc.AM_CONFIG_USE_LANDSCAPE)
    AM_CONFIG_USE_RUNTIME = AppVarReader(ConfigVariableDesc.AM_CONFIG_USE_RUNTIME)
    AM_CONFIG_USE_TOPOLOGY = AppVarReader(ConfigVariableDesc.AM_CONFIG_USE_CREDENTIALS)

    AM_CONFIG_DIRECTORY = AppVarReader(ConfigVariableDesc.AM_CONFIG_DIRECTORY)

    AM_CONFIG_PASS_PHRASE = AppVarReader(ConfigVariableDesc.AM_CONFIG_PASS_PHRASE)

    AM_CONFIG_CREDENTIAL_NAMES = AppVarReader(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_NAMES)
    AM_CONFIG_CREDENTIAL_URIS = AppVarReader(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_URIS)
    AM_CONFIG_CREDENTIAL_SOURCES = AppVarReader(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_SOURCES)
    AM_CONFIG_CREDENTIAL_FILES = AppVarReader(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_FILES)

    AM_CONFIG_DATAPROFILE_NAMES = AppVarReader(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_NAMES)
    AM_CONFIG_DATAPROFILE_URIS = AppVarReader(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_URIS)
    AM_CONFIG_DATAPROFILE_SOURCES = AppVarReader(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_SOURCES)
    AM_CONFIG_DATAPROFILE_FILES = AppVarReader(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_FILES)

    AM_CONFIG_LANDSCAPE_NAMES = AppVarReader(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_NAMES)
    AM_CONFIG_LANDSCAPE_URIS = AppVarReader(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_URIS)
    AM_CONFIG_LANDSCAPE_SOURCES = AppVarReader(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_SOURCES)
    AM_CONFIG_LANDSCAPE_FILES = AppVarReader(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_FILES)

    AM_CONFIG_TOPOLOGY_NAMES = AppVarReader(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_NAMES)
    AM_CONFIG_TOPOLOGY_URIS = AppVarReader(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_URIS)
    AM_CONFIG_TOPOLOGY_SOURCES = AppVarReader(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_SOURCES)
    AM_CONFIG_TOPOLOGY_FILES = AppVarReader(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_FILES)

    AM_CONFIG_RUNTIME_NAMES = AppVarReader(ConfigVariableDesc.AM_CONFIG_RUNTIME_NAMES)
    AM_CONFIG_RUNTIME_URIS = AppVarReader(ConfigVariableDesc.AM_CONFIG_RUNTIME_URIS)
    AM_CONFIG_RUNTIME_SOURCES = AppVarReader(ConfigVariableDesc.AM_CONFIG_RUNTIME_SOURCES)
    AM_CONFIG_RUNTIME_FILES = AppVarReader(ConfigVariableDesc.AM_CONFIG_RUNTIME_FILES)


def resolve_configuration_variables():

    # We need to resolve extension variables because we are
    # dependent on some of them.
    resolve_presence_variables()

    environ = os.environ

    this_app = ThisApplicationSingleton()
    this_app.resolve_variable_set(ConfigVariableDesc)

    ctx = ContextSingleton()

    # For now, we don't want to put the CREDENTIALS CONFIGURATION into the context, because at the moment we don't 
    # want to pass it around in the plain.  Possibly what we can do is create a version of MergeMap that will serialize
    # with a protective pass key or something like that.
    ctx.insert(ContextPaths.CONFIG_DATAPROFILES, CONFIGURATION_MAPS.DATAPROFILE_CONFIGURATION_MAP)
    ctx.insert(ContextPaths.CONFIG_LANDSCAPE, CONFIGURATION_MAPS.LANDSCAPE_CONFIGURATION_MAP)
    ctx.insert(ContextPaths.CONFIG_TOPOLOGY, CONFIGURATION_MAPS.TOPOLOGY_CONFIGURATION_MAP)
    ctx.insert(ContextPaths.CONFIG_RUNTIME, CONFIGURATION_MAPS.RUNTIME_CONFIGURATION_MAP)

    config_directory =  this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_DIRECTORY)

    # ====================== PROCESS CREDENTIAL VARIABLES ==============================

    use_credentials = False

    credential_files = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_FILES)
    credential_names = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_NAMES)
    credential_sources = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_SOURCES)
    require_credentials = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_CREDENTIALS)

    if len(credential_files) > 0 or len(credential_names) > 0 or require_credentials:
        use_credentials = True


    if len(credential_names) > 0 and len(credential_sources) == 0:
        credential_sources = [
            os.path.join(config_directory, "credentials")
        ]
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_SOURCES, credential_sources)


    if len(credential_files) > 0 or require_credentials:
        use_credentials = True
        
    this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_USE_CREDENTIALS, use_credentials)
    

    # ====================== PROCESS DATAPROFILE VARIABLES ==============================


    use_dataprofiles = False

    dataprofile_files = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_FILES)
    dataprofile_names = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_NAMES)
    dataprofile_sources = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_SOURCES)
    require_dataprofiles = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_DATAPROFILES)

    if len(dataprofile_files) > 0 or len(dataprofile_names) > 0:
        use_dataprofiles = True


    if len(dataprofile_names) > 0 and len(dataprofile_sources) == 0:
        dataprofile_sources = [
            os.path.join(config_directory, "dataprofiles")
        ]
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_SOURCES, dataprofile_sources)


    if len(dataprofile_files) > 0 or require_dataprofiles:
        use_dataprofiles = True
        
    this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_USE_DATAPROFILES, use_dataprofiles)


    # ====================== PROCESS LANDSCAPE VARIABLES ==============================


    use_landscapes = False

    landscape_files = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_FILES)
    landscape_names = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_NAMES)
    landscape_sources = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_SOURCES)
    require_landscape = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_LANDSCAPE)

    if len(landscape_files) > 0 or len(landscape_names) > 0:
        use_landscapes = True


    if len(landscape_names) > 0 and len(landscape_sources) == 0:
        landscape_sources = [
            os.path.join(config_directory, "landscapes")
        ]
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_SOURCES, landscape_sources)


    if len(landscape_files) > 0 or require_landscape:
        use_landscapes = True
        
    this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_USE_LANDSCAPE, use_landscapes)

    
    # ====================== PROCESS RUNTIME VARIABLES ==============================


    use_runtimes = False

    runtime_files = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_RUNTIME_FILES)
    runtime_names = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_RUNTIME_NAMES)
    runtime_sources = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_RUNTIME_SOURCES)
    require_runtime = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_RUNTIME)

    if len(runtime_files) > 0 or len(runtime_names) > 0:
        use_runtimes = True


    if len(runtime_names) > 0 and len(runtime_sources) == 0:
        runtime_sources = [
            os.path.join(config_directory, "runtimes")
        ]
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_RUNTIME_SOURCES, runtime_sources)


    if len(runtime_files) > 0 or require_runtime:
        use_runtimes = True
        
    this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_USE_RUNTIME, use_runtimes)


    # ====================== PROCESS TOPOLOGY VARIABLES ==============================


    use_topology = False

    topology_files = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_FILES)
    topology_names = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_NAMES)
    topology_sources = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_SOURCES)
    require_topology = this_app.get_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_TOPOLOGY)

    if len(topology_files) > 0 or len(topology_names) > 0:
        use_runtimes = True


    if len(topology_names) > 0 and len(topology_sources) == 0:
        topology_sources = [
            os.path.join(config_directory, "topologies")
        ]
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_SOURCES, topology_sources)


    if len(topology_files) > 0 or require_topology:
        use_topology = True
        
    this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_USE_TOPOLOGY, use_topology)


    return

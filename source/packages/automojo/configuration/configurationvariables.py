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

from automojo.thisapp.wellknown import ThisApplicationSingleton
from automojo.thisapp.appvardesc import AppVarDesc, VariableSource
from automojo.thisapp.appvaraccessor import AppVarAccessor
from automojo.thisapp.contextpaths import ContextPaths

from automojo.thisapp.personavariables import PersonaVariablesDesc, PersonaVariables

from automojo.configuration.configurationsettings import ConfigurationDefaults


from automojo.configuration.normalize import (
    split_and_normalize_name_list,
    split_and_normalize_path_list,
    split_and_normalize_source_list
)


class CONFIGURATION_MAPS:
    CREDENTIAL_CONFIGURATION_MAP = MergeMap()
    DATAPROFILE_CONFIGURATION_MAP = MergeMap()
    LANDSCAPE_CONFIGURATION_MAP = MergeMap()
    RUNTIME_CONFIGURATION_MAP = MergeMap(ConfigurationDefaults.DEFAULT_CONFIGURATION)
    TOPOLOGY_CONFIGURATION_MAP = MergeMap()



DEFAULT_CONFIGURATION = {
    "version": "1.0.0",
    "logging": {
        "levels": {
            "console": "INFO",
            "logfile": "DEBUG"
        }
    }
}

def default_config_directory():
    rtnval = os.path.join(PersonaVariables.AM_PRESENCE_DIR, "config")
    return rtnval

class ConfigVariablesDesc(PersonaVariablesDesc):

    AM_CONFIG_DIRECTORY = AppVarDesc(default=default_config_directory)
    AM_CONFIG_PASS_PHRASE = AppVarDesc(default=None)
    AM_CONFIG_STORAGE_URI = AppVarDesc(context_path=ContextPaths.CONFIG_STORAGE_URI, default="")


    AM_CONFIG_CREDENTIAL_NAMES = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_CREDENTIAL_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_CREDENTIAL_FILES = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_CREDENTIAL_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_CREDENTIAL_SOURCES = AppVarDesc(default="", context_path=ContextPaths.CONFIG_CREDENTIAL_SOURCES,
                                                converter=split_and_normalize_source_list)
    

    AM_CONFIG_DATAPROFILE_NAMES = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_DATAPROFILE_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_DATAPROFILE_FILES = AppVarDesc(context_path=ContextPaths.CONFIG_DATAPROFILE_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_DATAPROFILE_SOURCES = AppVarDesc(default="", context_path=ContextPaths.CONFIG_DATAPROFILE_SOURCES)
    

    AM_CONFIG_LANDSCAPE_NAMES = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_LANDSCAPE_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_LANDSCAPE_FILES = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_LANDSCAPE_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_LANDSCAPE_SOURCES = AppVarDesc(default="", context_path=ContextPaths.CONFIG_LANDSCAPE_SOURCES)
    

    AM_CONFIG_TOPOLOGY_NAMES = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_TOPOLOGY_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_TOPOLOGY_FILES = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_TOPOLOGY_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_TOPOLOGY_SOURCES = AppVarDesc(default="", context_path=ContextPaths.CONFIG_TOPOLOGY_SOURCES)
    

    AM_CONFIG_RUNTIME_NAMES = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_RUNTIME_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_RUNTIME_FILES = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_RUNTIME_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_RUNTIME_SOURCES = AppVarDesc(default="", context_path=ContextPaths.CONFIG_RUNTIME_SOURCES)
    

    AM_CONFIG_REQUIRE_CREDENTIALS = AppVarDesc(default=False, converter=parse_bool)
    AM_CONFIG_REQUIRE_DATAPROFILES = AppVarDesc(default=False, converter=parse_bool)
    AM_CONFIG_REQUIRE_LANDSCAPE = AppVarDesc(default=False, converter=parse_bool)
    AM_CONFIG_REQUIRE_RUNTIME = AppVarDesc(default=False, converter=parse_bool)
    AM_CONFIG_REQUIRE_TOPOLOGY = AppVarDesc(default=False, converter=parse_bool)


    AM_CONFIG_USE_CREDENTIALS = AppVarDesc(default=False, source=VariableSource.NONE)
    AM_CONFIG_USE_DATAPROFILES = AppVarDesc(default=False, source=VariableSource.NONE)
    AM_CONFIG_USE_LANDSCAPE = AppVarDesc(default=False, source=VariableSource.NONE)
    AM_CONFIG_USE_RUNTIME = AppVarDesc(default=False, source=VariableSource.NONE)
    AM_CONFIG_USE_TOPOLOGY = AppVarDesc(default=False, source=VariableSource.NONE)


    AM_CONFIG_CREDENTIAL_URIS = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_CREDENTIAL_URIS, source=VariableSource.NONE)
    AM_CONFIG_DATAPROFILE_URIS = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_DATAPROFILE_URIS, source=VariableSource.NONE)
    AM_CONFIG_LANDSCAPE_URIS = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_LANDSCAPE_URIS, source=VariableSource.NONE)
    AM_CONFIG_TOPOLOGY_URIS = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_TOPOLOGY_URIS, source=VariableSource.NONE)
    AM_CONFIG_RUNTIME_URIS = AppVarDesc(default=None, context_path=ContextPaths.CONFIG_RUNTIME_URIS, source=VariableSource.NONE)



class ConfigVariables(PersonaVariables):

    AM_CONFIG_REQUIRE_CREDENTIALS = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_REQUIRE_CREDENTIALS)
    AM_CONFIG_REQUIRE_DATAPROFILES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_REQUIRE_DATAPROFILES)
    AM_CONFIG_REQUIRE_LANDSCAPE = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_REQUIRE_LANDSCAPE)
    AM_CONFIG_REQUIRE_RUNTIME = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_REQUIRE_RUNTIME)
    AM_CONFIG_REQUIRE_TOPOLOGY = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_REQUIRE_TOPOLOGY)

    AM_CONFIG_STORAGE_URI = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_STORAGE_URI)

    AM_CONFIG_USE_CREDENTIALS = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_USE_CREDENTIALS)
    AM_CONFIG_USE_DATAPROFILES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_USE_DATAPROFILES)
    AM_CONFIG_USE_LANDSCAPE = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_USE_LANDSCAPE)
    AM_CONFIG_USE_RUNTIME = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_USE_RUNTIME)
    AM_CONFIG_USE_TOPOLOGY = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_USE_TOPOLOGY)

    AM_CONFIG_DIRECTORY = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_DIRECTORY)

    AM_CONFIG_PASS_PHRASE = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_PASS_PHRASE)

    AM_CONFIG_CREDENTIAL_NAMES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_NAMES)
    AM_CONFIG_CREDENTIAL_URIS = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_URIS)
    AM_CONFIG_CREDENTIAL_SOURCES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_SOURCES)
    AM_CONFIG_CREDENTIAL_FILES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_FILES)

    AM_CONFIG_DATAPROFILE_NAMES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_NAMES)
    AM_CONFIG_DATAPROFILE_URIS = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_URIS)
    AM_CONFIG_DATAPROFILE_SOURCES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_SOURCES)
    AM_CONFIG_DATAPROFILE_FILES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_FILES)

    AM_CONFIG_LANDSCAPE_NAMES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_NAMES)
    AM_CONFIG_LANDSCAPE_URIS = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_URIS)
    AM_CONFIG_LANDSCAPE_SOURCES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_SOURCES)
    AM_CONFIG_LANDSCAPE_FILES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_FILES)

    AM_CONFIG_TOPOLOGY_NAMES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_NAMES)
    AM_CONFIG_TOPOLOGY_URIS = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_URIS)
    AM_CONFIG_TOPOLOGY_SOURCES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_SOURCES)
    AM_CONFIG_TOPOLOGY_FILES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_FILES)

    AM_CONFIG_RUNTIME_NAMES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_RUNTIME_NAMES)
    AM_CONFIG_RUNTIME_URIS = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_RUNTIME_URIS)
    AM_CONFIG_RUNTIME_SOURCES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_RUNTIME_SOURCES)
    AM_CONFIG_RUNTIME_FILES = AppVarAccessor(ConfigVariablesDesc.AM_CONFIG_RUNTIME_FILES)


CONFIGURATION_VARIABLES_RESOLVED = False


def resolve_configuration_variables():

    global CONFIGURATION_VARIABLES_RESOLVED

    if CONFIGURATION_VARIABLES_RESOLVED:
        return
    
    CONFIGURATION_VARIABLES_RESOLVED = True

    this_app = ThisApplicationSingleton()
    this_app.resolve_variable_set(ConfigVariablesDesc)

    ctx = this_app.context

    # For now, we don't want to put the CREDENTIALS CONFIGURATION into the context, because at the moment we don't 
    # want to pass it around in the plain.  Possibly what we can do is create a version of MergeMap that will serialize
    # with a protective pass key or something like that.
    ctx.insert(ContextPaths.CONFIG_DATAPROFILES, CONFIGURATION_MAPS.DATAPROFILE_CONFIGURATION_MAP)
    ctx.insert(ContextPaths.CONFIG_LANDSCAPE, CONFIGURATION_MAPS.LANDSCAPE_CONFIGURATION_MAP)
    ctx.insert(ContextPaths.CONFIG_TOPOLOGY, CONFIGURATION_MAPS.TOPOLOGY_CONFIGURATION_MAP)
    ctx.insert(ContextPaths.CONFIG_RUNTIME, CONFIGURATION_MAPS.RUNTIME_CONFIGURATION_MAP)

    config_directory =  this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_DIRECTORY)

    # ====================== PROCESS CREDENTIAL VARIABLES ==============================

    use_credentials = False

    credential_files = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_FILES)
    credential_names = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_NAMES)
    credential_sources = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_SOURCES)
    require_credentials = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_REQUIRE_CREDENTIALS)

    if (credential_files is not None and len(credential_files) > 0) or (credential_names is not None and len(credential_names) > 0) or \
        require_credentials:
        use_credentials = True


    if credential_names is not None and len(credential_names) > 0 and len(credential_sources) == 0:
        credential_sources = [
            os.path.join(config_directory, "credentials")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_CREDENTIAL_SOURCES, credential_sources)


    if len(credential_files) > 0 or require_credentials:
        use_credentials = True
        
    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_CREDENTIALS, use_credentials)
    

    # ====================== PROCESS DATAPROFILE VARIABLES ==============================


    use_dataprofiles = False

    dataprofile_files = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_FILES)
    dataprofile_names = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_NAMES)
    dataprofile_sources = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_SOURCES)
    require_dataprofiles = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_REQUIRE_DATAPROFILES)

    if (dataprofile_files is not None and len(dataprofile_files) > 0) or (dataprofile_names is not None and len(dataprofile_names) > 0) or \
        require_dataprofiles:
        use_dataprofiles = True


    if dataprofile_names is not None and len(dataprofile_names) > 0 and len(dataprofile_sources) == 0:
        dataprofile_sources = [
            os.path.join(config_directory, "dataprofiles")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_DATAPROFILE_SOURCES, dataprofile_sources)


    if len(dataprofile_files) > 0 or require_dataprofiles:
        use_dataprofiles = True
        
    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_DATAPROFILES, use_dataprofiles)


    # ====================== PROCESS LANDSCAPE VARIABLES ==============================


    use_landscapes = False

    landscape_files = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_FILES)
    landscape_names = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_NAMES)
    landscape_sources = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_SOURCES)
    require_landscape = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_REQUIRE_LANDSCAPE)

    if (landscape_files is not None and len(landscape_files)) > 0 or (landscape_names is not None and len(landscape_names) > 0) or \
        require_landscape:
        use_landscapes = True


    if landscape_names is not None and len(landscape_names) > 0 and len(landscape_sources) == 0:
        landscape_sources = [
            os.path.join(config_directory, "landscapes")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_LANDSCAPE_SOURCES, landscape_sources)


    if len(landscape_files) > 0 or require_landscape:
        use_landscapes = True
        
    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_LANDSCAPE, use_landscapes)

    
    # ====================== PROCESS RUNTIME VARIABLES ==============================


    use_runtimes = False

    runtime_files = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_RUNTIME_FILES)
    runtime_names = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_RUNTIME_NAMES)
    runtime_sources = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_RUNTIME_SOURCES)
    require_runtime = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_REQUIRE_RUNTIME)

    if (runtime_files is not None and len(runtime_files) > 0) or (runtime_names is not None and len(runtime_names) > 0) or \
        require_runtime:
        use_runtimes = True


    if runtime_names is not None and len(runtime_names) > 0 and len(runtime_sources) == 0:
        runtime_sources = [
            os.path.join(config_directory, "runtimes")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_RUNTIME_SOURCES, runtime_sources)


    if len(runtime_files) > 0 or require_runtime:
        use_runtimes = True
        
    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_RUNTIME, use_runtimes)


    # ====================== PROCESS TOPOLOGY VARIABLES ==============================


    use_topology = False

    topology_files = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_FILES)
    topology_names = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_NAMES)
    topology_sources = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_SOURCES)
    require_topology = this_app.get_variable_value(ConfigVariablesDesc.AM_CONFIG_REQUIRE_TOPOLOGY)

    if (topology_files is not None and len(topology_files) > 0) or (topology_names is not None and len(topology_names) > 0) or \
        require_topology:
        use_topology = True


    if topology_names is not None and len(topology_names) > 0 and len(topology_sources) == 0:
        topology_sources = [
            os.path.join(config_directory, "topologies")
        ]
        this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_TOPOLOGY_SOURCES, topology_sources)


    if len(topology_files) > 0 or require_topology:
        use_topology = True
        
    this_app.override_variable_value(ConfigVariablesDesc.AM_CONFIG_USE_TOPOLOGY, use_topology)


    return

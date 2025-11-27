"""
.. module:: constants
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module which contains the :class:`AM_CONFIG_VARIABLE_NAMES` enumeration of config related variable names.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import os

from automojo.xmodules.xconvert import parse_bool
from automojo.xmodules.xvariables import VariableDesc, VariableSource

from automojo.presence.constants import PresenceVariableDesc
from automojo.presence.contextpaths import ContextPaths


from automojo.configuration.normalize import (
    split_and_normalize_name_list,
    split_and_normalize_path_list,
    split_and_normalize_source_list
)

DEFAULT_CONFIGURATION = {
    "version": "1.0.0",
    "logging": {
        "levels": {
            "console": "INFO",
            "logfile": "DEBUG"
        }
    }
}

class ConfigVariableDesc(PresenceVariableDesc):

    AM_CONFIG_DIRECTORY = VariableDesc(default=os.path.join(PresenceVariableDesc.AM_PRESENCE_DIRECTORY.default, "config"))
    AM_CONFIG_PASS_PHRASE = VariableDesc()
    AM_CONFIG_STORAGE_URI = VariableDesc(context_path=ContextPaths.CONFIG_STORAGE_URI, default="")


    AM_CONFIG_CREDENTIAL_NAMES = VariableDesc(context_path=ContextPaths.CONFIG_CREDENTIAL_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_CREDENTIAL_FILES = VariableDesc(context_path=ContextPaths.CONFIG_CREDENTIAL_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_CREDENTIAL_SOURCES = VariableDesc(context_path=ContextPaths.CONFIG_CREDENTIAL_SOURCES, default="",
                                                converter=split_and_normalize_source_list)
    

    AM_CONFIG_DATAPROFILE_NAMES = VariableDesc(context_path=ContextPaths.CONFIG_DATAPROFILE_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_DATAPROFILE_FILES = VariableDesc(context_path=ContextPaths.CONFIG_DATAPROFILE_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_DATAPROFILE_SOURCES = VariableDesc(context_path=ContextPaths.CONFIG_DATAPROFILE_SOURCES, default="")
    

    AM_CONFIG_LANDSCAPE_NAMES = VariableDesc(context_path=ContextPaths.CONFIG_LANDSCAPE_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_LANDSCAPE_FILES = VariableDesc(context_path=ContextPaths.CONFIG_LANDSCAPE_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_LANDSCAPE_SOURCES = VariableDesc(context_path=ContextPaths.CONFIG_LANDSCAPE_SOURCES, default="")
    

    AM_CONFIG_TOPOLOGY_NAMES = VariableDesc(context_path=ContextPaths.CONFIG_TOPOLOGY_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_TOPOLOGY_FILES = VariableDesc(context_path=ContextPaths.CONFIG_TOPOLOGY_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_TOPOLOGY_SOURCES = VariableDesc(context_path=ContextPaths.CONFIG_TOPOLOGY_SOURCES, default="")
    

    AM_CONFIG_RUNTIME_NAMES = VariableDesc(context_path=ContextPaths.CONFIG_RUNTIME_NAMES, converter=split_and_normalize_name_list)
    AM_CONFIG_RUNTIME_FILES = VariableDesc(context_path=ContextPaths.CONFIG_RUNTIME_FILES, converter=split_and_normalize_path_list)
    AM_CONFIG_RUNTIME_SOURCES = VariableDesc(context_path=ContextPaths.CONFIG_RUNTIME_SOURCES, default="")
    

    AM_CONFIG_REQUIRE_CREDENTIALS = VariableDesc(default=False, converter=parse_bool)
    AM_CONFIG_REQUIRE_DATAPROFILES = VariableDesc(default=False, converter=parse_bool)
    AM_CONFIG_REQUIRE_LANDSCAPE = VariableDesc(default=False, converter=parse_bool)
    AM_CONFIG_REQUIRE_RUNTIME = VariableDesc(default=False, converter=parse_bool)
    AM_CONFIG_REQUIRE_TOPOLOGY = VariableDesc(default=False, converter=parse_bool)


    AM_CONFIG_USE_CREDENTIALS = VariableDesc(default=False, source=VariableSource.NONE)
    AM_CONFIG_USE_DATAPROFILES = VariableDesc(default=False, source=VariableSource.NONE)
    AM_CONFIG_USE_LANDSCAPE = VariableDesc(default=False, source=VariableSource.NONE)
    AM_CONFIG_USE_RUNTIME = VariableDesc(default=False, source=VariableSource.NONE)
    AM_CONFIG_USE_TOPOLOGY = VariableDesc(default=False, source=VariableSource.NONE)


    AM_CONFIG_CREDENTIAL_URIS = VariableDesc(context_path=ContextPaths.CONFIG_CREDENTIAL_URIS, source=VariableSource.NONE)
    AM_CONFIG_DATAPROFILE_URIS = VariableDesc(context_path=ContextPaths.CONFIG_DATAPROFILE_URIS, source=VariableSource.NONE)
    AM_CONFIG_LANDSCAPE_URIS = VariableDesc(context_path=ContextPaths.CONFIG_LANDSCAPE_URIS, source=VariableSource.NONE)
    AM_CONFIG_TOPOLOGY_URIS = VariableDesc(context_path=ContextPaths.CONFIG_TOPOLOGY_URIS, source=VariableSource.NONE)
    AM_CONFIG_RUNTIME_URIS = VariableDesc(context_path=ContextPaths.CONFIG_RUNTIME_URIS, source=VariableSource.NONE)


"""
.. module:: optionoverrides
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Defines configuration option override helpers and constants.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import List

from automojo.presence.contextpaths import ContextPaths
from automojo.presence.wellknown import ThisApplicationSingleton

from automojo.configuration.normalize import SEPARATOR, normalize_file_path_list, normalize_source_path_list

from automojo.configuration.constants import ConfigVariableDesc

from automojo.configuration.configurationsettings import AM_CONFIG_DEFAULTS
from automojo.configuration.configurationvariables import AM_CONFIG_VARIABLES


class ConfigOptionOverrides:

    @staticmethod
    def override_config_credentials_names(credential_names: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_CREDENTIALS_NAMES
            variable and context configuration setting.

            :param landscape_names: The names of the credential configs to use when creating the credential config.
        """
        this_app = ThisApplicationSingleton()
        
        strval = SEPARATOR.join(credential_names)

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_NAMES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_CREDENTIALS, "True")
        
        return

    @staticmethod
    def override_config_credentials_sources(sources: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_CREDENTIALS_SOURCES
            variable and context configuration setting.

            :param sources: The uri(s) of to use as the credential config search uri(s).
        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(sources))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_SOURCES, strval)
        return

    @staticmethod
    def override_config_credentials_files(filepaths: List[str]):
        """
            The override function used to override the AM_CONFIG_CREDENTIAL_FILES variable and update
            the context configuration setting.

            :param filepaths: A list of file paths for configuration files.
        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(filepaths))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_CREDENTIAL_SOURCES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_CREDENTIALS, "True")
        return
    
    @staticmethod
    def override_config_dataprofile_names(dataprofile_names: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_DATAPROFILE_NAMES
            variable and context configuration setting.

            :param landscape_names: The names of the credential configs to use when creating the credential config.
        """
        this_app = ThisApplicationSingleton()
        
        strval = SEPARATOR.join(dataprofile_names)

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_NAMES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_DATAPROFILES, "True")
        
        return

    @staticmethod
    def override_config_dataprofile_sources(sources: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_DATAPROFILE_SOURCES
            variable and context configuration setting.

            :param sources: The uri(s) of to use as the credential config search uri(s).
        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(sources))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_SOURCES, strval)
        return

    @staticmethod
    def override_config_dataprofile_files(filepaths: List[str]):
        """
            The override function used to override the AM_CONFIG_DATAPROFILE_FILES variable and update
            the context configuration setting.

            :param filepaths: A list of file paths for configuration files.
        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(filepaths))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_DATAPROFILE_SOURCES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_DATAPROFILES, "True")
        return

    @staticmethod
    def override_config_landscape_names(landscape_names: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_LANDSCAPE_NAMES
            variable and context configuration setting.

            :param landscape_names: The names of the landscape configs to use when creating the landscape config.
        """
        this_app = ThisApplicationSingleton()
        
        strval = SEPARATOR.join(landscape_names)

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_NAMES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_LANDSCAPE, "True")
        return

    @staticmethod
    def override_config_landscape_sources(sources: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_LANDSCAPE_SOURCES
            variable and context configuration setting.

            :param sources: The uri(s) of to use as the landscape config search uri(s).
        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(sources))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_SOURCES, strval)
        return

    @staticmethod
    def override_config_landscape_files(filepaths: List[str]):
        """
            The override function used to override the AM_CONFIG_LANDSCAPE_FILES variable and update
            the context configuration setting.

            :param filepaths: A list of file paths for configuration files.
        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(filepaths))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_LANDSCAPE_SOURCES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_LANDSCAPE, "True")
        return

    @staticmethod
    def override_config_runtime_names(runtime_names: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_RUNTIME_NAMES
            variable and context configuration setting.

            :param runtime_names: The names of the runtime files to use when selecting runtime files.
        """
        this_app = ThisApplicationSingleton()
        
        strval = SEPARATOR.join(runtime_names)

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_RUNTIME_NAMES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_RUNTIME, "True")
        return

    @staticmethod
    def override_config_runtime_sources(sources: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_RUNTIME_SOURCES
            variable and context configuration setting.

            :param sources: The uri(s) of to use as the runtime config search uri(s).

        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(sources))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_RUNTIME_SOURCES, strval)
        return

    @staticmethod
    def override_config_runtime_files(filepaths: List[str]):
        """
            The override function used to override the AM_CONFIG_RUNTIME_FILES variable and update
            the context configuration setting.

            :param filepaths: A list of file paths for configuration files.
        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(filepaths))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_RUNTIME_SOURCES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_RUNTIME, "True")
        return


    @staticmethod
    def override_config_topology_names(topology_names: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_TOPOLOGY_NAMES
            variable and context configuration setting.

            :param topology_names: The names of the topology files to use when selecting topology files.
        """
        this_app = ThisApplicationSingleton()
        
        strval = SEPARATOR.join(topology_names)

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_NAMES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_TOPOLOGY, "True")
        return

    @staticmethod
    def override_config_topology_sources(sources: List[str]):
        """
            This override function provides a mechanism overriding the AM_CONFIG_TOPOLOGY_SOURCES
            variable and context configuration setting.

            :param sources: The uri(s) of to use as the topology config search uri(s).
        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(sources))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_SOURCES, strval)
        return

    @staticmethod
    def override_config_topology_files(filepaths: List[str]):
        """
            The override function used to override the AM_CONFIG_TOPOLOGY_FILES variable and update
            the context configuration setting.

            :param filepaths: A list of file paths for configuration files.
        """
        this_app = ThisApplicationSingleton()

        strval = SEPARATOR.join(normalize_source_path_list(filepaths))

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_TOPOLOGY_SOURCES, strval)
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_TOPOLOGY, "True")
        return

    @staticmethod
    def override_configuration_requirements(require_credentials: bool=False,
            require_landscape: bool=False, require_runtime: bool=False, require_topology: bool=False,
            require_dataprofiles: bool=False):
        """
            Called before or after activating the runtime in order to modify the required configuration
            files based on the applicaiton or run requirements.

            :param require_credentials: Indicates a credentials configuration file is required.
            :param require_landscape: Indicates a landscape configuration file is required.
            :param require_runtime: Indicates a runtime configuration file is required.
            :param require_topology: Indicates a topology configuration file is required.
            :param require_dataprofiles: Indicates a dataprofile configuration file is required.
        """
        this_app = ThisApplicationSingleton()

        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_CREDENTIALS, repr(require_credentials))
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_LANDSCAPE, repr(require_landscape))
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_RUNTIME, repr(require_runtime))
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_TOPOLOGY, repr(require_topology))
        this_app.override_variable_value(ConfigVariableDesc.AM_CONFIG_REQUIRE_DATAPROFILES, repr(require_dataprofiles))
        
        return

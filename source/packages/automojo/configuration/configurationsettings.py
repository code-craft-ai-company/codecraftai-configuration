"""
.. module:: overrides
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains an enumeration of environment variable names
               that are used by the configuration code.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional

from automojo.presence.wellknown import ThisApplicationSingleton

from automojo.presence.presencesettings import establish_presence_settings, AM_PRESENCE_DEFAULTS

default_config = {}

class ConfigurationDefaults:

    AM_CONFIG_REQUIRE_CREDENTIALS = False
    if "AM_CONFIG_REQUIRE_CREDENTIALS" in default_config:
        AM_CONFIG_REQUIRE_CREDENTIALS = default_config["AM_CONFIG_REQUIRE_CREDENTIALS"]

    AM_CONFIG_REQUIRE_DATAPROFILES = False
    if "AM_CONFIG_REQUIRE_DATAPROFILES" in default_config:
        AM_CONFIG_REQUIRE_DATAPROFILES = default_config["AM_CONFIG_REQUIRE_DATAPROFILES"]

    AM_CONFIG_REQUIRE_LANDSCAPE = False
    if "AM_CONFIG_REQUIRE_LANDSCAPE" in default_config:
        AM_CONFIG_REQUIRE_LANDSCAPE = default_config["AM_CONFIG_REQUIRE_LANDSCAPE"]

    AM_CONFIG_REQUIRE_RUNTIME = False
    if "AM_CONFIG_REQUIRE_RUNTIME" in default_config:
        AM_CONFIG_REQUIRE_RUNTIME = default_config["AM_CONFIG_REQUIRE_RUNTIME"]

    AM_CONFIG_REQUIRE_TOPOLOGY = False
    if "AM_CONFIG_REQUIRE_TOPOLOGY" in default_config:
        AM_CONFIG_REQUIRE_TOPOLOGY = default_config["AM_CONFIG_REQUIRE_TOPOLOGY"]

    AM_CONFIG_STORAGE_URI = ""
    if "AM_CONFIG_STORAGE_URI" in default_config:
        AM_CONFIG_STORAGE_URI = default_config["AM_CONFIG_STORAGE_URI"]

    DEFAULT_CONFIGURATION = {
        "version": "1.0.0",
        "logging": {
            "levels": {
                "console": "INFO",
                "logfile": "DEBUG"
            }
        }
    }


CONFIG_SETTINGS_ESTABLISHED = False

def establish_configuration_settings(*, name: Optional[str]=None, home_dir: Optional[str]=None,  settings_file: Optional[str]=None,
                                     extension_modules: Optional[str]=None, logger_name: Optional[str]=None, log_basename: Optional[str]=None,
                                     log_directory: Optional[str]=None, service_name: Optional[str]=None, default_configuration: Optional[dict]=None,
                                    **other):

    global CONFIG_SETTINGS_ESTABLISHED

    if not CONFIG_SETTINGS_ESTABLISHED:
        CONFIG_SETTINGS_ESTABLISHED = True

        establish_presence_settings(name=name, home_dir=home_dir, settings_file=settings_file, extension_modules=extension_modules,
                                    logger_name=logger_name, log_basename=log_basename, log_directory=log_directory,
                                    service_name=service_name, **other)

        if default_configuration is not None:
            AM_CONFIG_DEFAULTS.DEFAULT_CONFIGURATION = default_configuration

    return


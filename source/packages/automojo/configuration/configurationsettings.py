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

from automojo.presence.wellknown import ConfigParserSingleton
from automojo.presence.presencesettings import establish_presence_settings, AM_PRESENCE_DEFAULTS

default_config = {}

config = ConfigParserSingleton()
if "AUTOMOJO-CONFIG" in config:
    default_config = config["AUTOMOJO-CONFIG"]

class AM_CONFIG_DEFAULTS(AM_PRESENCE_DEFAULTS):

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

def establish_configuration_settings(*, name: Optional[str]=None, home_dir: Optional[str]=None,  settings_file: Optional[str]=None, extension_modules: Optional[str]=None, default_configuration: Optional[dict]=None, **other):

    global CONFIG_SETTINGS_ESTABLISHED

    if not CONFIG_SETTINGS_ESTABLISHED:
        CONFIG_SETTINGS_ESTABLISHED = True

        establish_presence_settings(name=name, home_dir=home_dir, settings_file=settings_file, extension_modules=extension_modules, **other)

        if default_configuration is not None:
            AM_CONFIG_DEFAULTS.DEFAULT_CONFIGURATION = default_configuration

    return
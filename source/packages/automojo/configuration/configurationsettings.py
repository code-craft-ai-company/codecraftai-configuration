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
            ConfigurationDefaults.DEFAULT_CONFIGURATION = default_configuration

    return


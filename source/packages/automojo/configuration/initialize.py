"""
.. module:: initialize
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that contains override mechanisms for the environment variable
               names used to initialize a global context for a python application

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional

from automojo.configuration.configurationsettings import establish_configuration_settings

class AM_CONFIGURATION_STATE:
    INITIALIZED = False


def initialize_configuration(*, name: Optional[str]=None, home_dir: Optional[str]=None, settings_file: Optional[str]=None,
                       extension_modules: Optional[str]=None, logger_name: Optional[str]=None, default_configuration: dict=None,
                       service_name: Optional[str]=None, **other):

    # =======================================================================================
    # The way we start up the test framework and the order which things come up in is a very
    # important part of the automation process.  It effects whether or not logging is brought
    # up consistently before all modules start using it.  It ensures that no matter how we
    # enter into an automation process, whether via a test runner, terminal, or debugging a single
    # file that we properly parse arguments and settings and launch the automation process
    # consistently.
    

    AM_CONFIGURATION_STATE.INITIALIZED = True

    establish_configuration_settings(name=name, home_dir=home_dir, settings_file=settings_file, extension_modules=extension_modules,
                                     logger_name=logger_name, default_configuration=default_configuration, service_name=service_name, **other)
    
    from automojo.configuration.configurationvariables import resolve_configuration_variables

    # The runtime variables can tell us where to find extensions, so we must resolve the runtime
    # varaibles before attempting to resolve any extension factories.
    resolve_configuration_variables()

    return



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Tuple, Union

from abc import abstractmethod, ABC

from automojo.configuration.configurationformat import ConfigurationFormat

class ConfigurationSourceBase(ABC):

    scheme: str = "not-set"

    def __init__(self, uri: str):
        """
            Initializes the configuration source base with its source URI.

            :param uri: The URI identifying the configuration source.
        """
        self._uri = uri
        return

    @property
    def uri(self):
        """
            The URI identifying the configuration source.
        """
        return self._uri

    @abstractmethod
    def parse(self, uri: str) -> Union[None, "ConfigurationSourceBase"]:
        """
            Parses a URI and returns a configuration source instance if
            the URI is valid for the implementing source type.

            :param uri: Source URI to parse.

            :returns: A configuration source instance or ``None``.
        """
        return

    @abstractmethod
    def try_load_configuration(self, config_name: str) -> Union[Tuple[ConfigurationFormat, dict], Tuple[None, None]]:
        """
            Attempts to load a configuration by name.

            :param config_name: Name of the configuration to load.

            :returns: Tuple of configuration format and configuration data or
                      ``(None, None)`` if not found.
        """
        return


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Dict, Optional, Tuple, Union

import http
import re
import json
import yaml

import requests

from ccai.configuration.configurationformat import ConfigurationFormat
from ccai.configuration.sources.configurationsourcebase import (
    ConfigurationSourceBase
)

EXTENSION_TO_CONFIG_FORMAT = {
    "yml": ConfigurationFormat.YAML,
    "yaml": ConfigurationFormat.YAML,
    "json": ConfigurationFormat.JSON
}


class HttpSource(ConfigurationSourceBase):

    scheme = "http"
    secure_scheme = "https"

    parse_http_exp = re.compile(r"http://(?P<baseurl>[\S]+)")
    parse_https_exp = re.compile(r"https://(?P<baseurl>[\S]+)")

    def __init__(self, uri: str):
        """
            Initializes an HTTP configuration source.

            :param uri: HTTP or HTTPS URI of the configuration location.
        """
        super().__init__(uri)
        return

    @classmethod
    def parse(cls, uri: str) -> Union[None, "HttpSource"]:
        """
            Parses an HTTP(S) source URI.

            :param uri: URI to parse.

            :returns: A :class:`HttpSource` instance or ``None``.
        """

        rtnobj = None

        mobj = cls.parse_http_exp.match(uri)
        if mobj is not None:
            rtnobj = HttpSource(uri)
        
        mobj = cls.parse_https_exp.match(uri)
        if mobj is not None:
            rtnobj = HttpSource(uri)

        return rtnobj
    
    def try_load_configuration(self, config_name: str, credentials: Optional[Dict[str, Tuple[str, str]]] = None) -> Union[Tuple[ConfigurationFormat, dict], Tuple[None, None]]:
        """
            Attempts to load a configuration from an HTTP(S) endpoint.

            :param config_name: Name of the configuration to load.
            :param credentials: Optional mapping of credentials; ignored here.

            :returns: Tuple of configuration format and data or ``(None, None)``.
        """
        config_info = None
        config_format = None

        baseurl = self._uri.rstrip("/")

        for ext in ["yaml", "yml", "json"]:
            checkurl = f"{baseurl}/{config_name}.{ext}"
            resp = requests.get(checkurl)

            if resp.status_code == http.HTTPStatus.OK:
                config_format = EXTENSION_TO_CONFIG_FORMAT[ext]
                config_content = resp.content
                if config_format == ConfigurationFormat.YAML:
                    config_info = yaml.safe_load(config_content)
                elif config_format == ConfigurationFormat.JSON:
                    config_info = json.loads(config_content)
                break

        return config_format, config_info

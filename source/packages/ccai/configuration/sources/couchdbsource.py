
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Dict, Optional, Tuple, Union

import logging
import re
import traceback

from ccai.errors.exceptions import ConfigurationError

from ccai.configuration.configurationformat import ConfigurationFormat
from ccai.configuration.sources.configurationsourcebase import (
    ConfigurationSourceBase
)

logger = logging.getLogger()

class CouchDBSource(ConfigurationSourceBase):

    scheme = "couchdb"
    parse_exp = re.compile(r"couchdb://(?P<scheme>[htps]+)\+(?P<host>[a-zA-Z\.0-9\-]+)(?P<port>[:0-9]+)*/(?P<database>[a-zA-Z\.0-9\-]+)")

    def __init__(self, uri: str, cscheme: str, host: str, database: str, port: Optional[int]):
        """
            Creates a configuration source that loads documents from CouchDB.

            :param uri: Original URI string.
            :param cscheme: Connection scheme ``http`` or ``https``.
            :param host: Host name of the CouchDB server.
            :param database: Database name containing configurations.
            :param port: Optional port for the server.
        """
        super().__init__(uri)
        self._cscheme = cscheme
        self._host = host
        self._database = database
        self._port = port
        return

    @property
    def database(self) -> str:
        """
            Database name containing configurations.
        """
        return self._database

    @property
    def host(self) -> str:
        """
            Host name of the CouchDB server.
        """
        return self._host

    @property
    def port(self) -> int:
        """
            Port number for the CouchDB server.
        """
        return self._port

    @classmethod
    def parse(cls, uri: str) -> Union[None, "CouchDBSource"]:
        """
            Parses a CouchDB source URI.

            :param uri: URI to parse.

            :returns: A :class:`CouchDBSource` instance or ``None``.
        """

        rtnobj = None

        mobj = cls.parse_exp.match(uri)
        if mobj is not None:
            try:
                import couchdb
            except ImportError:
                errmsg = "You must install the 'couchdb' module in order to use couchdb sources."
                raise ConfigurationError(errmsg)

            matchinfo = mobj.groupdict()

            cscheme = matchinfo["scheme"]
            host = matchinfo["host"]

            port = None
            if "port" in matchinfo and matchinfo["port"] is not None:
                port = int(matchinfo["port"].lstrip(":"))
            
            database = matchinfo["database"]

            rtnobj = CouchDBSource(uri, cscheme, host, database, port)

        return rtnobj
    
    def try_load_configuration(self, config_name: str, credentials: Dict[str, Tuple[str, str]]) -> Union[Tuple[ConfigurationFormat, dict], Tuple[None, None]]:
        """
            Attempts to load a configuration document from CouchDB.

            :param config_name: Name of the configuration document.
            :param credentials: Mapping of host names to ``(user, password)`` pairs.

            :returns: Tuple of configuration format and data or ``(None, None)``.
        """
        config_info = None
        config_format = None

        try:
            dburi = None
            
            if self._port is not None:
                dburi = f"{self._cscheme}://{self._host}:{self._port}/{self._database}"
            else:
                dburi = f"{self._cscheme}://{self._host}/{self._database}"

            import couchdb

            db = couchdb.Database(dburi)

            if credentials is not None and self._host in credentials:
                username, password = credentials[self._host]
                db.resource.credentials = (username, password)

            config_info = db.get(config_name)
            config_format = ConfigurationFormat.JSON

        except Exception as xcpt:
            errmsg = traceback.format_exc()
            logger.error(errmsg)
            config_info = None

        return config_format, config_info

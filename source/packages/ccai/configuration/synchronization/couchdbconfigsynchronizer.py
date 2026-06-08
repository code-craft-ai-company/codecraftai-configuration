

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Dict, Tuple, Union

import re

from ccai.errors.exceptions import ConfigurationError

from ccai.configuration.synchronization.configsynchronizerbase import ConfigSynchronizerBase


class CouchDbConfigSynchronizer(ConfigSynchronizerBase):
    """
        A couchdb configuration synchronizer.

        couchdb://https+somehost.eng.com:8888/somedb-prefix

        ..note: For couchdb, the configurations are stored in a database under a database which is a combination of the
                the 'database prefix' declared in the storage-uri combined with the venue.  For example, 'configdb-azure'.
                The configuration documents are stored with names based on the remaining grouping parameters.  The document
                name consists of the '<user>-<config-class>-<config-name>'.  For example 'myron-landscapes-apod-picluster'.
    """

    scheme = "couchdb"
    parse_exp = re.compile(r"couchdb://(?P<scheme>[htps]+)\+(?P<host>[a-zA-Z\.0-9\-]+)(?P<port>[:0-9]+)*/(?P<database_prefix>[a-zA-Z\.0-9\-]+)")

    def __init__(self, storage_uri: str, scheme: str, host: str, port: Union[int, None], database_prefix: str):
        """
            Initializes a CouchDB configuration synchronizer.

            :param storage_uri: Original storage URI.
            :param scheme: HTTP scheme for CouchDB.
            :param host: Host name of the CouchDB server.
            :param port: Optional port number.
            :param database_prefix: Prefix for database names.
        """
        super().__init__(storage_uri)

        self._storage_uri = storage_uri
        self._scheme = scheme
        self._host = host
        self._port = port
        self._database_prefix = database_prefix
        return

    @classmethod
    def parse(cls, uri: str) -> Union[None, "CouchDbConfigSynchronizer"]:
        """
            Parses a CouchDB configuration synchronizer URI.

            :param uri: URI to parse.

            :returns: A :class:`CouchDbConfigSynchronizer` instance or ``None``.
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

            scheme = matchinfo["scheme"]
            host = matchinfo["host"]

            port = None
            if "port" in matchinfo and matchinfo["port"] is not None:
                port = int(matchinfo["port"].lstrip(":"))
            
            database_prefix = matchinfo["database_prefix"]

            rtnobj = CouchDbConfigSynchronizer(uri, scheme, host, port, database_prefix)

        return rtnobj

    def _publish_configuration(self, venue: str, user: str, config_class: str, config_name: str, config_format: str, config_info: str, credentials: Dict[str, Tuple[str, str]]):
        """
            Publish a configuration document to CouchDB.

            :param venue: Venue identifier for the configuration.
            :param user: User name used to namespace the configuration.
            :param config_class: Configuration class folder name.
            :param config_name: Name of the configuration document.
            :param config_format: File format ``json`` or ``yaml``.
            :param config_info: Configuration data to persist.
            :param credentials: Mapping of host to ``(user, password)`` pairs.
        """

        database = f"{self._database_prefix}={venue}"
        dburi = None
            
        if self._port is not None:
            dburi = f"{self._scheme}://{self._host}:{self._port}/{database}"
        else:
            dburi = f"{self._scheme}://{self._host}/{database}"

        document_name = f"{config_class}-{user}-{config_name}"

        import couchdb

        db = couchdb.Database(dburi)

        if credentials is not None and self._host in credentials:
            username, password = credentials[self._host]
            db.resource.credentials = (username, password)

        document_info = {
            "_id": document_name,
            "format": config_format,
            "config": config_info
        }

        config_info = db.save(document_info)

        return

    def _retrieve_configuration(self, venue: str, user: str, config_class: str, config_name: str, credentials: Dict[str, Tuple[str, str]]) -> Union[Tuple[str, dict], Tuple[None, None]]:
        """
            Retrieve a configuration document from CouchDB.

            :param venue: Venue identifier for the configuration.
            :param user: User name used to namespace the configuration.
            :param config_class: Configuration class folder name.
            :param config_name: Name of the configuration document.
            :param credentials: Mapping of host to ``(user, password)`` pairs.

            :returns: Tuple of configuration format and data or ``(None, None)``.
        """

        config_format = None
        config_info = None

        database = f"{self._database_prefix}={venue}"
        dburi = None
            
        if self._port is not None:
            dburi = f"{self._scheme}://{self._host}:{self._port}/{database}"
        else:
            dburi = f"{self._scheme}://{self._host}/{database}"

        document_name = f"{config_class}-{user}-{config_name}"

        import couchdb

        db = couchdb.Database(dburi)

        if credentials is not None and self._host in credentials:
            username, password = credentials[self._host]
            db.resource.credentials = (username, password)

        document_info = db.get(document_name)

        config_format = document_info["format"]
        config_info = document_info["config"]

        return config_format, config_info
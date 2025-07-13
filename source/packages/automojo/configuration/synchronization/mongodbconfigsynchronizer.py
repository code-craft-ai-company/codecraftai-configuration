

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Dict, Tuple, Union

import re

from urllib.parse import quote_plus

from automojo.errors.exceptions import ConfigurationError

from automojo.configuration.synchronization.configsynchronizerbase import ConfigSynchronizerBase

class MongoDbConfigSynchronizer(ConfigSynchronizerBase):
    """
        A directory configuration synchronizer.
    """

    scheme = "mongodb"
    parse_exp = re.compile(r"mongodb://(?P<host>[a-zA-Z\.0-9\-]+)/(?P<database>[a-zA-Z\.0-9\-]+)")

    def __init__(self, storage_uri: str, scheme: str, host: str, port: Union[int, None], database: str, verify_certificate: bool = True):
        """
            Initializes a MongoDB configuration synchronizer.

            :param storage_uri: Original storage URI.
            :param scheme: Connection scheme for MongoDB.
            :param host: Host name of the server.
            :param port: Optional port value.
            :param database: Name of the database.
            :param verify_certificate: Controls TLS certificate verification.
        """
        super().__init__(storage_uri)

        self._scheme = scheme
        self._host = host
        self._port = port
        self._database = database
        self._verify_certificate = verify_certificate
        return

    @classmethod
    def parse(cls, uri: str, verify_certificate: bool = True) -> Union[None, "MongoDbConfigSynchronizer"]:
        """
            Parses a MongoDB synchronizer URI.

            :param uri: URI to parse.
            :param verify_certificate: Controls TLS certificate verification.

            :returns: A :class:`MongoDbConfigSynchronizer` instance or ``None``.
        """

        rtnobj = None

        mobj = cls.parse_exp.match(uri)
        if mobj is not None:
            try:
                import pymongo
            except ImportError:
                errmsg = "You must install the 'pymongo' module in order to use couchdb sources."
                raise ConfigurationError(errmsg)

            matchinfo = mobj.groupdict()

            scheme = matchinfo["scheme"]
            host = matchinfo["host"]

            port = None
            if "port" in matchinfo and matchinfo["port"] is not None:
                port = int(matchinfo["port"].lstrip(":"))
            
            database = matchinfo["database"]

            rtnobj = MongoDbConfigSynchronizer(uri, scheme, host, port, database, verify_certificate=verify_certificate)

        return rtnobj

    def _publish_configuration(self, venue: str, user: str, config_class: str, config_name: str, config_format: str, config_info: str, credentials: Dict[str, Tuple[str, str]]):
        """
            Publish a configuration document to MongoDB.

            :param venue: Venue identifier for the configuration.
            :param user: User name used to namespace the configuration.
            :param config_class: Configuration class folder name.
            :param config_name: Name of the configuration document.
            :param config_format: File format ``json`` or ``yaml``.
            :param config_info: Configuration data to persist.
            :param credentials: Mapping of host to ``(user, password)`` pairs.
        """
        
        username, password = credentials[self._host]
        dburi = f"mongodb+srv://{username}:{quote_plus(password)}@{self._host}/?retryWrites=true&w=majority"

        document_name = f"{config_class}-{user}-{config_name}"

        document_info = {
            "_id": document_name,
            "format": config_format,
            "config": config_info
        }

        import pymongo

        client = pymongo.MongoClient(dburi)

        try:
            db = client[self._database]

            collection = db[venue]
            
            collection.insert_one(document_info)
        finally:
            client.close()

        return
    
    def _retrieve_configuration(self, venue: str, user: str, config_class: str, config_name: str, credentials: Dict[str, Tuple[str, str]]) -> Union[Tuple[str, dict], Tuple[None, None]]:
        """
            Retrieve a configuration document from MongoDB.

            :param venue: Venue identifier for the configuration.
            :param user: User name used to namespace the configuration.
            :param config_class: Configuration class folder name.
            :param config_name: Name of the configuration document.
            :param credentials: Mapping of host to ``(user, password)`` pairs.

            :returns: Tuple of configuration format and data or ``(None, None)``.
        """
        
        config_format = None
        config_info = None

        username, password = credentials[self._host]
        dburi = f"mongodb+srv://{username}:{quote_plus(password)}@{self._host}/?retryWrites=true&w=majority"

        document_name = f"{config_class}-{user}-{config_name}"

        import pymongo

        client = pymongo.MongoClient(dburi, tlsAllowInvalidCertificates=self._verify_certificate)

        try:
            db = client[self._database]

            collection = db[venue]

            document_info = collection.find_one({"_id": config_name})

            config_format = document_info["format"]
            config_info = document_info["config"]
        finally:
            client.close()

        return config_format, config_info
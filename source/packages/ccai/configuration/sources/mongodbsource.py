
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Dict, Tuple, Union

import logging
import re

from urllib.parse import quote_plus

from ccai.errors.exceptions import ConfigurationError

from ccai.configuration.configurationformat import ConfigurationFormat
from ccai.configuration.sources.configurationsourcebase import (
    ConfigurationSourceBase
)

logger = logging.getLogger()

class MongoDBSource(ConfigurationSourceBase):

    scheme = "mongodb"
    parse_exp = re.compile(r"mongodb://(?P<host>[a-zA-Z\.0-9\-]+)/(?P<database>[a-zA-Z\.0-9\-]+)/(?P<collection>[a-zA-Z\.0-9\-]+)")

    def __init__(self, uri: str, host: str, database: str, collection: str, verify_certificate: bool = True):
        """
            Initializes a MongoDB configuration source.

            :param uri: Source URI string.
            :param host: MongoDB host name.
            :param database: Database containing configurations.
            :param collection: Collection where configurations are stored.
            :param verify_certificate: Controls TLS certificate verification.
        """
        super().__init__(uri)
        self._host = host
        self._database = database
        self._collection = collection
        self._verify_certificate = verify_certificate
        return
    
    @property
    def collection(self) -> str:
        """
            Name of the MongoDB collection storing configurations.
        """
        return self._collection

    @property
    def database(self) -> str:
        """
            Name of the MongoDB database containing configurations.
        """
        return self._database

    @property
    def host(self) -> str:
        """
            Host name of the MongoDB server.
        """
        return self._host

    @property
    def port(self) -> int:
        """
            Port number for the MongoDB server.
        """
        return self._port

    @classmethod
    def parse(cls, uri: str, verify_certificate: bool = True) -> Union[None, "MongoDBSource"]:
        """
            Parses a MongoDB source URI.

            :param uri: URI to parse.
            :param verify_certificate: Controls TLS certificate verification.

            :returns: A :class:`MongoDBSource` instance or ``None``.
        """

        rtnobj = None

        mobj = cls.parse_exp.match(uri)
        if mobj is not None:
            try:
                import pymongo
            except ImportError:
                errmsg = "You must install the 'pymongo' module in order to use mongodb sources."
                raise ConfigurationError(errmsg)

            matchinfo = mobj.groupdict()
            host = matchinfo["host"]
            database = matchinfo["database"]
            collection = matchinfo["collection"]
            rtnobj = MongoDBSource(uri, host, database, collection, verify_certificate=verify_certificate)

        return rtnobj

    def try_load_configuration(self, config_name: str, credentials: Dict[str, Tuple[str, str]]) -> Union[Tuple[ConfigurationFormat, dict], Tuple[None, None]]:
        """
            Attempts to load a configuration document from MongoDB.

            :param config_name: Name of the configuration to load.
            :param credentials: Mapping of host names to ``(user, password)`` pairs.

            :returns: Tuple of configuration format and data or ``(None, None)``.
        """
        config_info = None
        config_format = None

        try:
            username, password = credentials[self._host]
            dburi = f"mongodb+srv://{username}:{quote_plus(password)}@{self._host}/?retryWrites=true&w=majority"

            import pymongo

            client = pymongo.MongoClient(dburi, connect=False)

            try:
                db = client[self._database]

                collection = db[self._collection]

                config_info = collection.find_one({"_id": config_name})
                config_format = ConfigurationFormat.JSON

            finally:
                client.close()

        except Exception as xcpt:
            import traceback
            errmsg = traceback.format_exc()
            logger.error(errmsg)
            config_info = None


        return config_format, config_info

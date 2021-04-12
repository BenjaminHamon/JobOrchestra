import os
import platform
import re
from typing import Callable, Optional

import pymongo
import sqlalchemy

from bhamon_orchestra_model.database.database_administration import DatabaseAdministration
from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.database.json_database_administration import JsonDatabaseAdministration
from bhamon_orchestra_model.database.json_database_client import JsonDatabaseClient
from bhamon_orchestra_model.database.mongo_database_administration import MongoDatabaseAdministration
from bhamon_orchestra_model.database.mongo_database_client import MongoDatabaseClient
from bhamon_orchestra_model.database.sql_database_administration import SqlDatabaseAdministration
from bhamon_orchestra_model.database.sql_database_client import SqlDatabaseClient
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer


def create_database_administration_factory(
		database_uri: str, database_metadata: Optional[sqlalchemy.schema.MetaData]) -> Callable[[],DatabaseAdministration]:

	if database_uri.startswith("json://"):
		serializer = JsonSerializer(indent = 4)
		data_directory = _convert_uri_to_local_path(database_uri)
		return lambda: JsonDatabaseAdministration(serializer, data_directory)

	if database_uri.startswith("mongodb://"):
		return lambda: MongoDatabaseAdministration(pymongo.MongoClient(database_uri))

	if database_uri.startswith("postgresql://"):
		database_engine = sqlalchemy.create_engine(database_uri)
		return lambda: SqlDatabaseAdministration(database_engine.connect(), database_metadata)

	raise ValueError("Unsupported database uri '%s'" % database_uri)


def create_database_client_factory(
		database_uri: str, database_metadata: Optional[sqlalchemy.schema.MetaData]) -> Callable[[],DatabaseClient]:

	if database_uri.startswith("json://"):
		serializer = JsonSerializer(indent = 4)
		data_directory = _convert_uri_to_local_path(database_uri)
		return lambda: JsonDatabaseClient(serializer, data_directory)

	if database_uri.startswith("mongodb://"):
		return lambda: MongoDatabaseClient(pymongo.MongoClient(database_uri))

	if database_uri.startswith("postgresql://"):
		database_engine = sqlalchemy.create_engine(database_uri)
		return lambda: SqlDatabaseClient(database_engine.connect(), database_metadata)

	raise ValueError("Unsupported database uri '%s'" % database_uri)


def _convert_uri_to_local_path(database_uri: str) -> str:
	database_uri_regex = re.compile(r"^json://(?P<path>/[a-zA-Z0-9_\-\./%]+)$")
	if platform.system() == "Windows":
		database_uri_regex = re.compile(r"^json:///(?P<path>[a-zA-Z]:[a-zA-Z0-9_\-\./%]+)$")

	database_uri_match = database_uri_regex.search(database_uri)
	if database_uri_match is None:
		raise ValueError("URI is invalid or unsupported: '%s'" % database_uri)

	return os.path.normpath(database_uri_match.group("path"))

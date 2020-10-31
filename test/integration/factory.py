import re

import pymongo
import sqlalchemy

from bhamon_orchestra_model.database.json_database_administration import JsonDatabaseAdministration
from bhamon_orchestra_model.database.json_database_client import JsonDatabaseClient
from bhamon_orchestra_model.database.mongo_database_administration import MongoDatabaseAdministration
from bhamon_orchestra_model.database.mongo_database_client import MongoDatabaseClient
from bhamon_orchestra_model.database.sql_database_administration import SqlDatabaseAdministration
from bhamon_orchestra_model.database.sql_database_client import SqlDatabaseClient


def create_database_administration_factory(database_uri, database_metadata):
	if database_uri.startswith("json://"):
		return lambda: JsonDatabaseAdministration(re.sub("^json://", "", database_uri))
	if database_uri.startswith("mongodb://"):
		return lambda: MongoDatabaseAdministration(pymongo.MongoClient(database_uri))
	if database_uri.startswith("postgresql://"):
		database_engine = sqlalchemy.create_engine(database_uri)
		return lambda: SqlDatabaseAdministration(database_engine.connect(), database_metadata)
	raise ValueError("Unsupported database uri '%s'" % database_uri)


def create_database_client_factory(database_uri, database_metadata):
	if database_uri.startswith("json://"):
		return lambda: JsonDatabaseClient(re.sub("^json://", "", database_uri))
	if database_uri.startswith("mongodb://"):
		return lambda: MongoDatabaseClient(pymongo.MongoClient(database_uri))
	if database_uri.startswith("postgresql://"):
		database_engine = sqlalchemy.create_engine(database_uri)
		return lambda: SqlDatabaseClient(database_engine.connect(), database_metadata)
	raise ValueError("Unsupported database uri '%s'" % database_uri)

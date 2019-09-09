import logging
import os
import re
import sys
import uuid

import pymongo

from bhamon_build_model.json_database_client import JsonDatabaseClient
from bhamon_build_model.mongo_database_client import MongoDatabaseClient


log_format = "[{levelname}][{name}] {message}"


def configure_logging(log_level):
	logging.basicConfig(level = log_level, format = log_format, style = "{")
	logging.addLevelName(logging.DEBUG, "Debug")
	logging.addLevelName(logging.INFO, "Info")
	logging.addLevelName(logging.WARNING, "Warning")
	logging.addLevelName(logging.ERROR, "Error")
	logging.addLevelName(logging.CRITICAL, "Critical")

	logging.getLogger("asyncio").setLevel(logging.INFO)
	logging.getLogger("filelock").setLevel(logging.WARNING)
	logging.getLogger("urllib3").setLevel(logging.INFO)
	logging.getLogger("websockets.protocol").setLevel(logging.INFO)
	logging.getLogger("werkzeug").setLevel(logging.WARNING)


def create_database_client(database_uri):
	if database_uri.startswith("json://"):
		return JsonDatabaseClient(re.sub("^json://", "", database_uri))
	if database_uri.startswith("mongodb://"):
		return MongoDatabaseClient(pymongo.MongoClient(database_uri).get_database())
	raise ValueError("Unsupported database uri '%s'" % database_uri)


def load_environment():
	return {
		"python3_executable": sys.executable,
		"build_service_url": "http://localhost:5902",
	}


def load_test_context_environment(temporary_directory, database_type):
	database_uri = get_test_context_database_uri(temporary_directory, database_type) if database_type is not None else None

	return {
		"master_address": "localhost",
		"master_port": 5901,
		"service_address": "localhost",
		"service_port": 5902,
		"website_address": "localhost",
		"website_port": 5903,
		"database_uri": database_uri,
	}


def get_test_context_database_uri(temporary_directory, database_type):
	run_identifier = uuid.UUID(os.path.basename(os.path.dirname(temporary_directory)))
	database_name = "test_build_database_" + str(run_identifier)

	if database_type == "json":
		return "json://" + os.path.join(temporary_directory, "master")
	if database_type == "mongo":
		return "mongodb://localhost:27017/" + database_name
	raise ValueError("Unsupported database type '%s'" % database_type)


def get_all_database_types():
	return [ "json", "mongo" ]

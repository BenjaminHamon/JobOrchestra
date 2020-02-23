import logging

import pymongo


logger = logging.getLogger("DatabaseController")


def register_commands(subparsers):
	command_parser = subparsers.add_parser("initialize-database", help = "initialize the database")
	command_parser.add_argument("--simulate", action = "store_true", help = "perform a simulation (dry-run)")
	command_parser.set_defaults(handler = initialize_database)


def initialize_database(application, arguments):
	if application.database_uri.startswith("json://"):
		initialize_json_database(application.database_uri, arguments.simulate)
	elif application.database_uri.startswith("mongodb://"):
		initialize_mongo_database(application.database_uri, application.database_authentication, arguments.simulate)
	else:
		raise ValueError("Unsupported database uri '%s'" % application.database_uri)


def initialize_json_database(database_uri, simulate):
	logger.info("Initializing Json database (Uri: '%s')" + (" (simulation)" if simulate else ""), database_uri) # pylint: disable = logging-not-lazy


def initialize_mongo_database(database_uri, database_authentication, simulate):
	logger.info("Initializing Mongo database (Uri: '%s')" + (" (simulation)" if simulate else ""), database_uri) # pylint: disable = logging-not-lazy
	database = pymongo.MongoClient(database_uri, **database_authentication).get_database()

	print("")

	logger.info("Creating run index")
	if not simulate:
		database["run"].create_index([ ("project", pymongo.ASCENDING), ("identifier", pymongo.ASCENDING) ], name = "identifier_unique", unique = True)

	logger.info("Creating job index")
	if not simulate:
		database["job"].create_index([ ("project", pymongo.ASCENDING), ("identifier", pymongo.ASCENDING) ], name = "identifier_unique", unique = True)

	logger.info("Creating schedule index")
	if not simulate:
		database["schedule"].create_index([ ("project", pymongo.ASCENDING), ("identifier", pymongo.ASCENDING) ], name = "identifier_unique", unique = True)

	logger.info("Creating task index")
	if not simulate:
		database["task"].create_index("identifier", name = "identifier_unique", unique = True)

	logger.info("Creating user index")
	if not simulate:
		database["user"].create_index("identifier", name = "identifier_unique", unique = True)

	logger.info("Creating worker index")
	if not simulate:
		database["worker"].create_index("identifier", name = "identifier_unique", unique = True)

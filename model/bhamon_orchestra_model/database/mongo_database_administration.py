import logging
from typing import List, Tuple

from bson.codec_options import CodecOptions
import pymongo

from bhamon_orchestra_model.database.database_administration import DatabaseAdministration


logger = logging.getLogger("MongoDatabaseAdministration")


class MongoDatabaseAdministration(DatabaseAdministration):
	""" Administration client for a MongoDB database. """


	def __init__(self, mongo_client: pymongo.MongoClient) -> None:
		self.mongo_client = mongo_client


	def __enter__(self):
		return self


	def __exit__(self, exception_type, exception_value, traceback):
		self.close()


	def initialize(self, simulate: bool = False) -> None:
		logger.info("Initializing" + (" (simulation)" if simulate else "")) # pylint: disable = logging-not-lazy

		logger.info("Creating run index")
		if not simulate:
			self.create_index("run", "identifier_unique", [ ("project", "ascending"), ("identifier", "ascending") ], is_unique = True)

		logger.info("Creating job index")
		if not simulate:
			self.create_index("job", "identifier_unique", [ ("project", "ascending"), ("identifier", "ascending") ], is_unique = True)

		logger.info("Creating schedule index")
		if not simulate:
			self.create_index("schedule", "identifier_unique", [ ("project", "ascending"), ("identifier", "ascending") ], is_unique = True)

		logger.info("Creating user index")
		if not simulate:
			self.create_index("user", "identifier_unique", [ ("identifier", "ascending") ], is_unique = True)

		logger.info("Creating worker index")
		if not simulate:
			self.create_index("worker", "identifier_unique", [ ("identifier", "ascending") ], is_unique = True)


	def upgrade(self, simulate: bool = False) -> None:
		logger.info("Upgrading" + (" (simulation)" if simulate else "")) # pylint: disable = logging-not-lazy

		database = self.mongo_client.get_database(codec_options = CodecOptions(tz_aware = True))

		logger.info("Renaming build table to run")
		if "build" in database.collection_names():
			if not simulate:
				database["build"].rename("run")

		logger.info("Updating run project and job fields")
		for run in database["run"].find():
			if "project" not in run:
				project, job = run["job"].split("_", 1)
				logger.info("Run %s: Job %s => Project %s, Job %s", run["identifier"], run["job"], project, job)
				if not simulate:
					database["run"].update_one({ "identifier": run["identifier"] }, { "$set": { "project": project, "job": job } })

		logger.info("Fix missing fields for user authentications")
		if not simulate:
			database["user_authentication"].update_many({ "hash_function_salt": { "$exists": False } }, { "$set": { "hash_function_salt": None } })
			database["user_authentication"].update_many({ "expiration_date": { "$exists": False } }, { "$set": { "expiration_date": None } })

		logger.info("Fix missing fields for runs")
		if not simulate:
			database["run"].update_many({ "source": { "$exists": False } }, { "$set": { "source": None } })
			database["run"].update_many({ "worker": { "$exists": False } }, { "$set": { "worker": None } })
			database["run"].update_many({ "start_date": { "$exists": False } }, { "$set": { "start_date": None } })
			database["run"].update_many({ "completion_date": { "$exists": False } }, { "$set": { "completion_date": None } })
			database["run"].update_many({ "results": { "$exists": False } }, { "$set": { "results": None } })
			database["run"].update_many({ "should_abort": { "$exists": False } }, { "$set": { "should_abort": False } })
			database["run"].update_many({ "should_cancel": { "$exists": False } }, { "$set": { "should_cancel": False } })

		logger.info("Fix missing fields for workers")
		if not simulate:
			database["worker"].update_many({ "should_disconnect": { "$exists": False } }, { "$set": { "should_disconnect": False } })

		logger.info("Remove steps from runs")
		if not simulate:
			database["run"].update_many({ "steps": { "$exists": True } }, { "$unset": { "steps": None } })

		logger.info("Remove steps and workspace from jobs")
		if not simulate:
			database["job"].update_many({ "steps": { "$exists": True } }, { "$unset": { "steps": None } })
			database["job"].update_many({ "workspace": { "$exists": True } }, { "$unset": { "workspace": None } })


	def create_index(self, table: str, identifier: str, field_collection: List[Tuple[str,str]], is_unique: bool = False) -> None:
		mongo_field_collection = []
		for field, direction in field_collection:
			if direction in [ "asc", "ascending" ]:
				mongo_field_collection.append((field, pymongo.ASCENDING))
			elif direction in [ "desc", "descending" ]:
				mongo_field_collection.append((field, pymongo.DESCENDING))

		database = self.mongo_client.get_database(codec_options = CodecOptions(tz_aware = True))
		database[table].create_index(mongo_field_collection, name = identifier, unique = is_unique)


	def close(self) -> None:
		self.mongo_client.close()

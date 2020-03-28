import logging

from typing import List, Tuple

import pymongo


logger = logging.getLogger("MongoDatabaseAdministration")


class MongoDatabaseAdministration:
	""" Administration client for a MongoDB database. """


	def __init__(self, mongo_client: pymongo.MongoClient) -> None:
		self.mongo_client = mongo_client


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

		logger.info("Renaming build table to run")
		if "build" in self.mongo_client.get_database().collection_names():
			if not simulate:
				self.mongo_client.get_database()["build"].rename("run")

		logger.info("Ensure run worker fields exist")
		if not simulate:
			self.mongo_client.get_database()["run"].update_many({ "worker": { "$exists": False } }, { "$set": { "worker": None } })

		logger.info("Updating run project and job fields")
		for run in self.mongo_client.get_database()["run"].find():
			if "project" not in run:
				project, job = run["job"].split("_", 1)
				logger.info("Run %s: Job %s => Project %s, Job %s", run["identifier"], run["job"], project, job)
				if not simulate:
					self.mongo_client.get_database()["run"].update_one({ "identifier": run["identifier"] }, { "$set": { "project": project, "job": job } })


	def create_index(self, table: str, identifier: str, field_collection: List[Tuple[str,str]], is_unique: bool = False) -> None:
		mongo_field_collection = []
		for field, direction in field_collection:
			if direction in [ "asc", "ascending" ]:
				mongo_field_collection.append((field, pymongo.ASCENDING))
			elif direction in [ "desc", "descending" ]:
				mongo_field_collection.append((field, pymongo.DESCENDING))

		self.mongo_client.get_database()[table].create_index(mongo_field_collection, name = identifier, unique = is_unique)


	def close(self) -> None:
		self.mongo_client.close()

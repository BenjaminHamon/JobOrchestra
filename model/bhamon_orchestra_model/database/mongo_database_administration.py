import logging

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
			self.mongo_client.get_database()["run"].create_index([ ("project", pymongo.ASCENDING), ("identifier", pymongo.ASCENDING) ], name = "identifier_unique", unique = True)

		logger.info("Creating job index")
		if not simulate:
			self.mongo_client.get_database()["job"].create_index([ ("project", pymongo.ASCENDING), ("identifier", pymongo.ASCENDING) ], name = "identifier_unique", unique = True)

		logger.info("Creating schedule index")
		if not simulate:
			self.mongo_client.get_database()["schedule"].create_index([ ("project", pymongo.ASCENDING), ("identifier", pymongo.ASCENDING) ], name = "identifier_unique", unique = True)

		logger.info("Creating user index")
		if not simulate:
			self.mongo_client.get_database()["user"].create_index("identifier", name = "identifier_unique", unique = True)

		logger.info("Creating worker index")
		if not simulate:
			self.mongo_client.get_database()["worker"].create_index("identifier", name = "identifier_unique", unique = True)


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

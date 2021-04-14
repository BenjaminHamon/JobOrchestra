import logging

import pymongo


logger = logging.getLogger("MongoMigration")

version = "2.0+9d4b6abb48"
date = "2020-05-03T14:00:24Z"


def upgrade(mongo_client: pymongo.MongoClient, simulate: bool = False) -> None:
	logger.info("Renaming build table to run")
	if "build" in mongo_client.get_database().collection_names():
		if not simulate:
			mongo_client.get_database()["build"].rename("run")

	logger.info("Ensure run worker fields exist")
	if not simulate:
		mongo_client.get_database()["run"].update_many({ "worker": { "$exists": False } }, { "$set": { "worker": None } })

	logger.info("Updating run project and job fields")
	for run in mongo_client.get_database()["run"].find():
		if "project" not in run:
			project, job = run["job"].split("_", 1)
			logger.info("Run %s: Job %s => Project %s, Job %s", run["identifier"], run["job"], project, job)
			if not simulate:
				mongo_client.get_database()["run"].update_one({ "identifier": run["identifier"] }, { "$set": { "project": project, "job": job } })

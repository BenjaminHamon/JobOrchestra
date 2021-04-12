import logging

import pymongo


logger = logging.getLogger("MongoMigration")

version = "3.0+427b2ed357"
date = "2021-03-13T10:26:24Z"


def upgrade(mongo_client: pymongo.MongoClient, simulate: bool = False) -> None:
	logger.info("Fix missing fields for user authentications")
	if not simulate:
		mongo_client.get_database()["user_authentication"].update_many({ "hash_function_salt": { "$exists": False } }, { "$set": { "hash_function_salt": None } })
		mongo_client.get_database()["user_authentication"].update_many({ "expiration_date": { "$exists": False } }, { "$set": { "expiration_date": None } })

	logger.info("Fix missing fields for runs")
	if not simulate:
		mongo_client.get_database()["run"].update_many({ "source": { "$exists": False } }, { "$set": { "source": None } })
		mongo_client.get_database()["run"].update_many({ "worker": { "$exists": False } }, { "$set": { "worker": None } })
		mongo_client.get_database()["run"].update_many({ "start_date": { "$exists": False } }, { "$set": { "start_date": None } })
		mongo_client.get_database()["run"].update_many({ "completion_date": { "$exists": False } }, { "$set": { "completion_date": None } })
		mongo_client.get_database()["run"].update_many({ "results": { "$exists": False } }, { "$set": { "results": None } })
		mongo_client.get_database()["run"].update_many({ "should_abort": { "$exists": False } }, { "$set": { "should_abort": False } })
		mongo_client.get_database()["run"].update_many({ "should_cancel": { "$exists": False } }, { "$set": { "should_cancel": False } })

	logger.info("Fix missing fields for workers")
	if not simulate:
		mongo_client.get_database()["worker"].update_many({ "should_disconnect": { "$exists": False } }, { "$set": { "should_disconnect": False } })

	logger.info("Remove steps from runs")
	if not simulate:
		mongo_client.get_database()["run"].update_many({ "steps": { "$exists": True } }, { "$unset": { "steps": None } })

	logger.info("Remove steps and workspace from jobs")
	if not simulate:
		mongo_client.get_database()["job"].update_many({ "steps": { "$exists": True } }, { "$unset": { "steps": None } })
		mongo_client.get_database()["job"].update_many({ "workspace": { "$exists": True } }, { "$unset": { "workspace": None } })

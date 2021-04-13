import logging

from bson.codec_options import CodecOptions
import dateutil.parser
import pymongo


logger = logging.getLogger("MongoMigration")

version = "4.0"
date = None


def upgrade(mongo_client: pymongo.MongoClient, simulate: bool = False) -> None:
	convert_datetimes(mongo_client, "project", "creation_date", simulate = simulate)
	convert_datetimes(mongo_client, "project", "update_date", simulate = simulate)
	convert_datetimes(mongo_client, "job", "creation_date", simulate = simulate)
	convert_datetimes(mongo_client, "job", "update_date", simulate = simulate)
	convert_datetimes(mongo_client, "run", "start_date", simulate = simulate)
	convert_datetimes(mongo_client, "run", "completion_date", simulate = simulate)
	convert_datetimes(mongo_client, "run", "creation_date", simulate = simulate)
	convert_datetimes(mongo_client, "run", "update_date", simulate = simulate)
	convert_datetimes(mongo_client, "schedule", "creation_date", simulate = simulate)
	convert_datetimes(mongo_client, "schedule", "update_date", simulate = simulate)
	convert_datetimes(mongo_client, "user", "creation_date", simulate = simulate)
	convert_datetimes(mongo_client, "user", "update_date", simulate = simulate)
	convert_datetimes(mongo_client, "user_authentication", "expiration_date", simulate = simulate)
	convert_datetimes(mongo_client, "user_authentication", "creation_date", simulate = simulate)
	convert_datetimes(mongo_client, "user_authentication", "update_date", simulate = simulate)
	convert_datetimes(mongo_client, "worker", "creation_date", simulate = simulate)
	convert_datetimes(mongo_client, "worker", "update_date", simulate = simulate)


def convert_datetimes(mongo_client: pymongo.MongoClient, table: str, key: str, simulate: bool = False) -> None:
	logger.info("Converting datetime '%s.%s'", table, key)

	database = mongo_client.get_database(codec_options = CodecOptions(tz_aware = True))

	table_entries = database[table].find({})

	for entry in table_entries:
		if entry[key] is not None:
			update_values = { key: dateutil.parser.parse(entry[key]) }

			if not simulate:
				database[table].update_one({ "_id": entry["_id"] }, { "$set": update_values })

import glob
import importlib
import logging
import os
import types
from typing import List, Optional, Tuple

from bson.codec_options import CodecOptions
import pymongo

import bhamon_orchestra_model
import bhamon_orchestra_model.database.migrations.mongo
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


	def get_metadata(self) -> dict:
		database = self.mongo_client.get_database(codec_options = CodecOptions(tz_aware = True))
		return database["__metadata__"].find_one({}, { "_id": False })


	def initialize(self, # pylint: disable = too-many-arguments
			product: Optional[str] = None,
			copyright: Optional[str] = None, # pylint: disable = redefined-builtin
			version: Optional[str] = None,
			date: Optional[str] = None,
			simulate: bool = False) -> None:

		logger.info("Initializing" + (" (simulation)" if simulate else "")) # pylint: disable = logging-not-lazy

		if self.get_metadata() is not None:
			raise RuntimeError("Database is already initialized")

		metadata = {
			"product": product if product is not None else bhamon_orchestra_model.__product__,
			"copyright": copyright if copyright is not None else bhamon_orchestra_model.__copyright__,
			"version": version if version is not None else bhamon_orchestra_model.__version__,
			"date": date if date is not None else bhamon_orchestra_model.__date__,
		}

		database = self.mongo_client.get_database(codec_options = CodecOptions(tz_aware = True))

		logger.info("Saving metadata")
		if not simulate:
			database["__metadata__"].insert_one(metadata)

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


	def upgrade(self, target_version: Optional[str] = None, simulate: bool = False) -> None:
		target_version = target_version if target_version is not None else bhamon_orchestra_model.__version__

		logger.info("Upgrading" + (" (simulation)" if simulate else "")) # pylint: disable = logging-not-lazy

		schema_metadata = self.get_metadata()
		if schema_metadata is None:
			raise RuntimeError("Database is not initialized")

		current_version = schema_metadata["version"].split("+")[0]
		target_version = target_version.split("+")[0]

		if current_version == target_version:
			logger.info("Database is already at target version %s", target_version)
			return

		logger.info("Upgrading from version %s to version %s", current_version, target_version)

		all_migrations = self.list_migrations()
		current_migration = next(migration for migration in all_migrations if migration.version.split("+")[0] == current_version)
		current_migration_index = all_migrations.index(current_migration)
		migrations_to_apply = all_migrations[current_migration_index + 1 :]

		for migration in migrations_to_apply:
			self.apply_migration(migration, simulate = simulate)


	def list_migrations(self) -> List[types.ModuleType]: # pylint: disable = no-self-use
		migration_module_base = bhamon_orchestra_model.database.migrations.mongo
		migration_directory = os.path.dirname(migration_module_base.__file__)

		all_migrations = []
		for file_path in glob.glob(os.path.join(migration_directory, "migration_*.py")):
			module_name = migration_module_base.__name__ + "." + os.path.basename(file_path)[:-3]
			all_migrations.append(importlib.import_module(module_name))

		all_migrations.sort(key = lambda migration: [ int(version_number) for version_number in migration.version.split("+")[0].split(".")])

		return all_migrations


	def apply_migration(self, migration: types.ModuleType, simulate: bool = False) -> None:
		logger.info("Applying migration to version %s", migration.version)

		migration.upgrade(self.mongo_client, simulate = simulate)

		logger.info("Saving metadata")

		database = self.mongo_client.get_database(codec_options = CodecOptions(tz_aware = True))
		metadata_entry = database["__metadata__"].find_one()

		metadata_update_data = {
			"version": migration.version,
			"date": migration.date,
		}

		if not simulate:
			database["__metadata__"].update_one({ "_id": metadata_entry["_id"] }, { "$set": metadata_update_data })


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

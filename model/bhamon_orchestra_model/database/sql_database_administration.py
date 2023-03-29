import glob
import importlib
import logging
import os
import types
from typing import List, Optional, Tuple

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Connection
from sqlalchemy.schema import MetaData

import bhamon_orchestra_model
import bhamon_orchestra_model.database.migrations.sql
from bhamon_orchestra_model.database.database_administration import DatabaseAdministration


logger = logging.getLogger("SqlDatabaseAdministration")


class SqlDatabaseAdministration(DatabaseAdministration):
	""" Administration client for a SQL database. """


	def __init__(self, connection: Connection, metadata: MetaData) -> None:
		self.connection = connection
		self.metadata = metadata


	def __enter__(self):
		return self


	def __exit__(self, exception_type, exception_value, traceback):
		self.close()


	def get_metadata(self) -> dict:
		try:
			schema_metadata_query = sqlalchemy.select(self.metadata.tables["__metadata__"])
			schema_metadata_rows = self.connection.execute(schema_metadata_query).mappings().fetchall()
		except SQLAlchemyError:
			return None

		if schema_metadata_rows == []:
			return None

		schema_metadata = {}
		for row in schema_metadata_rows:
			schema_metadata[row.key] = row.value

		return schema_metadata


	def initialize(self, # pylint: disable = too-many-arguments
			product: Optional[str] = None,
			copyright: Optional[str] = None, # pylint: disable = redefined-builtin
			version: Optional[str] = None,
			date: Optional[str] = None,
			simulate: bool = False) -> None:

		logger.info("Initializing" + (" (simulation)" if simulate else "")) # pylint: disable = logging-not-lazy

		if self.get_metadata() is not None:
			raise RuntimeError("Database is already initialized")

		schema_metadata = {
			"product": product if product is not None else bhamon_orchestra_model.__product__,
			"copyright": copyright if copyright is not None else bhamon_orchestra_model.__copyright__,
			"version": version if version is not None else bhamon_orchestra_model.__version__,
			"date": date if date is not None else bhamon_orchestra_model.__date__,
		}

		logger.info("Creating tables and indexes")
		if not simulate:
			self.metadata.create_all(self.connection.engine)

		logger.info("Saving metadata")

		schema_metadata_rows = []
		for key, value in schema_metadata.items():
			schema_metadata_rows.append({ "key": key, "value": value })

		query = sqlalchemy.insert(self.metadata.tables["__metadata__"]).values(schema_metadata_rows)
		if not simulate:
			self.connection.execute(query)


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


	def list_migrations(self) -> List[types.ModuleType]:
		migration_module_base = bhamon_orchestra_model.database.migrations.sql
		migration_directory = os.path.dirname(migration_module_base.__file__)

		all_migrations = []
		for file_path in glob.glob(os.path.join(migration_directory, "migration_*.py")):
			module_name = migration_module_base.__name__ + "." + os.path.basename(file_path)[:-3]
			all_migrations.append(importlib.import_module(module_name))

		all_migrations.sort(key = lambda migration: [ int(version_number) for version_number in migration.version.split("+")[0].split(".")])

		return all_migrations


	def apply_migration(self, migration: types.ModuleType, simulate: bool = False) -> None:
		logger.info("Applying migration to version %s", migration.version)

		context = MigrationContext.configure(self.connection)
		operations = Operations(context)

		with context.begin_transaction():
			migration.upgrade(operations, simulate = simulate)

			logger.info("Saving metadata")

			metadata_key_column = self.metadata.tables["__metadata__"].c.key

			version_query = sqlalchemy.update(self.metadata.tables["__metadata__"]).where(metadata_key_column == "version").values({ "value": migration.version })
			if not simulate:
				self.connection.execute(version_query)

			date_query = sqlalchemy.update(self.metadata.tables["__metadata__"]).where(metadata_key_column == "date").values({ "value": migration.date })
			if not simulate:
				self.connection.execute(date_query)


	def create_index(self, table: str, identifier: str, field_collection: List[Tuple[str,str]], is_unique: bool = False) -> None:
		raise NotImplementedError()


	def close(self) -> None:
		self.connection.close()

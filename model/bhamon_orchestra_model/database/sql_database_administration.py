import logging
from typing import List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Connection
from sqlalchemy.schema import MetaData

import bhamon_orchestra_model
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
			schema_metadata_query = self.metadata.tables["__metadata__"].select()
			schema_metadata_rows = self.connection.execute(schema_metadata_query).fetchall()
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

		query = self.metadata.tables["__metadata__"].insert(schema_metadata_rows)
		if not simulate:
			self.connection.execute(query)


	def upgrade(self, simulate: bool = False) -> None:
		raise NotImplementedError()


	def create_index(self, table: str, identifier: str, field_collection: List[Tuple[str,str]], is_unique: bool = False) -> None:
		raise NotImplementedError()


	def close(self) -> None:
		self.connection.close()

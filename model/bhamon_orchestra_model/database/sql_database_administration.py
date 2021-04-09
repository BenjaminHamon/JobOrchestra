import logging
from typing import List, Tuple

from sqlalchemy.engine import Connection
from sqlalchemy.schema import MetaData

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


	def initialize(self, simulate: bool = False) -> None:
		logger.info("Initializing" + (" (simulation)" if simulate else "")) # pylint: disable = logging-not-lazy

		if not simulate:
			self.metadata.create_all(self.connection.engine)


	def upgrade(self, simulate: bool = False) -> None:
		raise NotImplementedError()


	def create_index(self, table: str, identifier: str, field_collection: List[Tuple[str,str]], is_unique: bool = False) -> None:
		raise NotImplementedError()


	def close(self) -> None:
		self.connection.close()

import logging
from typing import List, Optional, Tuple

import sqlalchemy
from sqlalchemy.engine import Connection
from sqlalchemy.schema import MetaData
from sqlalchemy.sql import ClauseElement

from bhamon_orchestra_model.database.database_client import DatabaseClient


logger = logging.getLogger("SqlDatabaseClient")


class SqlDatabaseClient(DatabaseClient):
	""" Client for a SQL database. """


	def __init__(self, connection: Connection, metadata: MetaData) -> None:
		self.connection = connection
		self.metadata = metadata


	def count(self, table: str, filter: dict) -> int: # pylint: disable = redefined-builtin
		""" Return how many items are in a table, after applying a filter """

		where_clause = self._convert_filter(table, filter)
		query = sqlalchemy.select([ sqlalchemy.func.count() ]).select_from(self.metadata.tables[table]).where(where_clause)
		return self.connection.execute(query).scalar()


	def find_many(self, # pylint: disable = too-many-arguments
			table: str, filter: dict, # pylint: disable = redefined-builtin
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[List[Tuple[str,str]]] = None) -> List[dict]:
		""" Return a list of items from a table, after applying a filter, with options for limiting and sorting results """

		where_clause = self._convert_filter(table, filter)
		order_by_clauses = self._convert_order_by_expression(table, order_by)
		query = self.metadata.tables[table].select().where(where_clause).order_by(*order_by_clauses).offset(skip).limit(limit)
		result = self.connection.execute(query).fetchall()

		return [ dict(row) for row in result ]


	def find_one(self, table: str, filter: dict) -> Optional[dict]: # pylint: disable = redefined-builtin
		""" Return a single item (or nothing) from a table, after applying a filter """

		where_clause = self._convert_filter(table, filter)
		query = self.metadata.tables[table].select().where(where_clause).limit(1)
		result = self.connection.execute(query).fetchone()

		return dict(result) if result is not None else None


	def insert_one(self, table: str, data: dict) -> None:
		""" Insert a new item into a table """

		query = self.metadata.tables[table].insert(data)
		self.connection.execute(query)


	def insert_many(self, table: str, dataset: List[dict]) -> None:
		""" Insert a list of items into a table """

		query = self.metadata.tables[table].insert(dataset)
		self.connection.execute(query)


	def update_one(self, table: str, filter: dict, data: dict) -> None: # pylint: disable = redefined-builtin
		""" Update a single item (or nothing) from a table, after applying a filter """

		# It is not possible to use limit on a update query with SqlAlchemy,
		# so, in cases the filter matches several rows, we first find the row to delete then use its primary key to update it.

		row = self.find_one(table, filter)
		if row is None:
			return

		filter = { key: row[key] for key in [ column.name for column in self.metadata.tables[table].primary_key.columns ] }
		where_clause = self._convert_filter(table, filter)
		query = self.metadata.tables[table].update().where(where_clause).values(data)
		self.connection.execute(query)


	def delete_one(self, table: str, filter: dict) -> None: # pylint: disable = redefined-builtin
		""" Delete a single item (or nothing) from a table, after applying a filter """

		# It is not possible to use limit on a delete query with SqlAlchemy,
		# so, in cases the filter matches several rows, we first find the row to delete then use its primary key to delete it.

		row = self.find_one(table, filter)
		if row is None:
			return

		filter = { key: row[key] for key in [ column.name for column in self.metadata.tables[table].primary_key.columns ] }
		where_clause = self._convert_filter(table, filter)
		query = self.metadata.tables[table].delete().where(where_clause)
		self.connection.execute(query)


	def close(self) -> None:
		self.connection.close()


	def _convert_filter(self, table: str, filter: dict) -> ClauseElement: # pylint: disable = redefined-builtin
		all_conditions = []

		for key, value in filter.items():
			all_key_elements = key.split(".")
			key_selector = self.metadata.tables[table].columns[all_key_elements[0]]

			if len(all_key_elements) > 1:
				key_selector = key_selector[all_key_elements[1:]].as_string().cast(self._get_sqlalchemy_type(value))

			all_conditions.append(key_selector == value)

		return sqlalchemy.and_(*all_conditions)


	def _convert_order_by_expression(self, table: str, expression: Optional[List[Tuple[str,str]]]) -> List[ClauseElement]:
		""" Convert a order-by expression to its sqlalchemy representation """

		if expression is None:
			return []

		sql_order_by = []

		for key, direction in self._normalize_order_by_expression(expression):
			all_key_elements = key.split(".")
			key_selector = self.metadata.tables[table].columns[all_key_elements[0]]

			if len(all_key_elements) > 1:
				key_selector = key_selector[all_key_elements[1:]].as_string()

			if direction in [ "asc", "ascending" ]:
				sql_order_by.append(key_selector.asc().nullsfirst())
			elif direction in [ "desc", "descending" ]:
				sql_order_by.append(key_selector.desc().nullslast())

		return sql_order_by


	def _get_sqlalchemy_type(self, value): # pylint: disable = no-self-use
		if isinstance(value, bool):
			return sqlalchemy.Boolean
		if isinstance(value, float):
			return sqlalchemy.Float
		if isinstance(value, int):
			return sqlalchemy.Integer
		if isinstance(value, str):
			return sqlalchemy.String

		raise ValueError("Unsupported type: '%s'" % type(value))

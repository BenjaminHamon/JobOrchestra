import logging

from typing import List, Optional, Tuple

from bhamon_orchestra_model.database.database_client import DatabaseClient


logger = logging.getLogger("MemoryDatabaseClient")


class MemoryDatabaseClient(DatabaseClient):
	""" Client for a database storing data in memory, intended for development only. """


	def __init__(self) -> None:
		self.database = {}


	def count(self, table: str, filter: dict) -> int: # pylint: disable = redefined-builtin
		""" Return how many items are in a table, after applying a filter """
		return sum(1 for row in self.database.get(table, []) if self._match_filter(row, filter))


	def find_many(self, # pylint: disable = too-many-arguments
			table: str, filter: dict, # pylint: disable = redefined-builtin
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[Tuple[str,str]] = None) -> List[dict]:
		""" Return a list of items from a table, after applying a filter, with options for limiting and sorting results """

		start_index = skip
		end_index = (skip + limit) if limit is not None else None
		results = self.database.get(table, [])
		results = self._apply_order_by(results, order_by)
		results = [ row for row in results if self._match_filter(row, filter) ]
		return results[ start_index : end_index ]


	def find_one(self, table: str, filter: dict) -> Optional[dict]: # pylint: disable = redefined-builtin
		""" Return a single item (or nothing) from a table, after applying a filter """
		return next(( row for row in self.database.get(table, []) if self._match_filter(row, filter) ), None)


	def insert_one(self, table: str, data: dict) -> dict:
		""" Insert a new item into a table """

		if table not in self.database:
			self.database[table] = []
		self.database[table].append(data)


	def update_one(self, table: str, filter: dict, data: dict) -> None: # pylint: disable = redefined-builtin
		""" Update a single item (or nothing) from a table, after applying a filter """

		all_rows = self.database.get(table, [])
		matched_row = next(( row for row in all_rows if self._match_filter(row, filter) ), None)
		if matched_row is not None:
			matched_row.update(data)


	def delete_one(self, table: str, filter: dict) -> None: # pylint: disable = redefined-builtin
		""" Delete a single item (or nothing) from a table, after applying a filter """

		all_rows = self.database.get(table, [])
		matched_row = next(( row for row in all_rows if self._match_filter(row, filter) ), None)
		if matched_row is not None:
			all_rows.remove(matched_row)


	def _match_filter(self, row: dict, filter: dict) -> bool: # pylint: disable = no-self-use, redefined-builtin
		""" Check if an item matches a filter """

		for key, value in filter.items():
			data = row
			for key_part in key.split("."):
				if key_part not in data.keys():
					return False
				data = data[key_part]
			if data != value:
				return False
		return True


	def _apply_order_by(self, row_collection: List[dict], expression: Optional[List[Tuple[str,str]]]) -> List[dict]:
		""" Apply an order-by expression on a list of items """

		if expression is None:
			return row_collection

		for key, direction in reversed(self._normalize_order_by_expression(expression)):
			if direction in [ "asc", "ascending" ]:
				reverse = False
			elif direction in [ "desc", "descending" ]:
				reverse = True
			row_collection = sorted(row_collection, key = lambda x: x[key], reverse = reverse) # pylint: disable = cell-var-from-loop
		return row_collection

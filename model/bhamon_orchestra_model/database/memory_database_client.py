# pylint: disable = no-self-use, redefined-builtin

import logging

from bhamon_orchestra_model.database.database_client import DatabaseClient


logger = logging.getLogger("MemoryDatabaseClient")


class MemoryDatabaseClient(DatabaseClient):
	""" Client for a database storing data in memory, intended for development only. """


	def __init__(self):
		self.database = {}


	def count(self, table, filter):
		return sum(1 for row in self.database.get(table, []) if self._match_filter(row, filter))


	def find_many(self, table, filter, skip = 0, limit = None, order_by = None):
		start_index = skip
		end_index = (skip + limit) if limit is not None else None
		results = self.database.get(table, [])
		results = self._apply_order_by(results, order_by)
		results = [ row for row in results if self._match_filter(row, filter) ]
		return results[ start_index : end_index ]


	def find_one(self, table, filter):
		return next(( row for row in self.database.get(table, []) if self._match_filter(row, filter) ), None)


	def insert_one(self, table, data):
		if table not in self.database:
			self.database[table] = []
		self.database[table].append(data)


	def update_one(self, table, filter, data):
		all_rows = self.database.get(table, [])
		matched_row = next(( row for row in all_rows if self._match_filter(row, filter) ), None)
		if matched_row is not None:
			matched_row.update(data)


	def delete_one(self, table, filter):
		all_rows = self.database.get(table, [])
		matched_row = next(( row for row in all_rows if self._match_filter(row, filter) ), None)
		if matched_row is not None:
			all_rows.remove(matched_row)


	def _match_filter(self, row, filter):
		for key, value in filter.items():
			data = row
			for key_part in key.split("."):
				if key_part not in data.keys():
					return False
				data = data[key_part]
			if data != value:
				return False
		return True


	def _apply_order_by(self, row_collection, expression):
		if expression is None:
			return row_collection

		for key, direction in reversed(self._normalize_order_by_expression(expression)):
			if direction in [ "asc", "ascending" ]:
				reverse = False
			elif direction in [ "desc", "descending" ]:
				reverse = True
			row_collection = sorted(row_collection, key = lambda x: x[key], reverse = reverse) # pylint: disable = cell-var-from-loop
		return row_collection

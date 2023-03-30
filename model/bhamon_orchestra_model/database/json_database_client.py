import contextlib
import functools
import logging
import os
from typing import Any, List, Optional, Tuple, Union

import filelock

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer


logger = logging.getLogger("JsonDatabaseClient")


class JsonDatabaseClient(DatabaseClient):
	""" Client for a database storing data as json files, intended for development only. """


	def __init__(self, serializer: JsonSerializer, data_directory: str) -> None:
		self._serializer = serializer
		self.data_directory = data_directory
		self.lock_timeout = 5


	def count(self, table: str, filter: dict) -> int: # pylint: disable = redefined-builtin
		""" Return how many items are in a table, after applying a filter """

		with self._lock(table, timeout = self.lock_timeout):
			return sum(1 for row in self._load(table) if self._match_filter(row, filter))


	def find_many(self, # pylint: disable = too-many-arguments
			table: str, filter: dict, # pylint: disable = redefined-builtin
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[List[Tuple[str,str]]] = None) -> List[dict]:
		""" Return a list of items from a table, after applying a filter, with options for limiting and sorting results """

		with self._lock(table, timeout = self.lock_timeout):
			start_index = skip
			end_index = (skip + limit) if limit is not None else None
			results = self._load(table)
			results = self._apply_order_by(results, order_by)
			results = [ row for row in results if self._match_filter(row, filter) ]
			return results[ start_index : end_index ]


	def find_one(self, table: str, filter: dict) -> Optional[dict]: # pylint: disable = redefined-builtin
		""" Return a single item (or nothing) from a table, after applying a filter """

		with self._lock(table, timeout = self.lock_timeout):
			return next(( row for row in self._load(table) if self._match_filter(row, filter) ), None)


	def insert_one(self, table: str, data: dict) -> None:
		""" Insert a new item into a table """

		with self._lock(table, timeout = self.lock_timeout):
			all_indexes = self._load_indexes(table)
			all_rows = self._load(table)

			for index in [ x for x in all_indexes if x["is_unique"] ]:
				index_filter = { key: data[key] for key in index["field_collection"] }
				matched_row = next(( row for row in all_rows if self._match_filter(row, index_filter) ), None)

				if matched_row is not None:
					raise ValueError("Duplicate key '%s' in table '%s' for index '%s'" % (index_filter, table, index["identifier"]))

			all_rows.append(data)
			self._save(table, all_rows)


	def insert_many(self, table: str, dataset: List[dict]) -> None:
		""" Insert a list of items into a table """

		with self._lock(table, timeout = self.lock_timeout):
			all_indexes = self._load_indexes(table)
			all_rows = self._load(table)

			for data in dataset:
				for index in [ x for x in all_indexes if x["is_unique"] ]:
					index_filter = { key: data[key] for key in index["field_collection"] }
					matched_row = next(( row for row in all_rows if self._match_filter(row, index_filter) ), None)

					if matched_row is not None:
						raise ValueError("Duplicate key '%s' in table '%s' for index '%s'" % (index_filter, table, index["identifier"]))

			all_rows.extend(dataset)
			self._save(table, all_rows)


	def update_one(self, table: str, filter: dict, data: dict) -> None: # pylint: disable = redefined-builtin
		""" Update a single item (or nothing) from a table, after applying a filter """

		with self._lock(table, timeout = self.lock_timeout):
			all_rows = self._load(table)
			matched_row = next(( row for row in all_rows if self._match_filter(row, filter) ), None)
			if matched_row is not None:
				matched_row.update(data)
				self._save(table, all_rows)


	def delete_one(self, table: str, filter: dict) -> None: # pylint: disable = redefined-builtin
		""" Delete a single item (or nothing) from a table, after applying a filter """

		with self._lock(table, timeout = self.lock_timeout):
			all_rows = self._load(table)
			matched_row = next(( row for row in all_rows if self._match_filter(row, filter) ), None)
			if matched_row is not None:
				all_rows.remove(matched_row)
				self._save(table, all_rows)


	def close(self) -> None:
		""" Close the database connection """


	@contextlib.contextmanager
	def _lock(self, table: str, timeout: Union[int,float] = 5) -> None:
		""" Lock a table """

		file_path = os.path.join(self.data_directory, table + ".lock")
		os.makedirs(os.path.dirname(file_path), exist_ok = True)
		with filelock.FileLock(file_path, timeout = timeout):
			yield


	def _load(self, table: str) -> List[dict]:
		""" Load all items from a table """

		file_path = os.path.join(self.data_directory, table + ".json")
		table_data = None

		try:
			table_data = self._serializer.deserialize_from_file(file_path)
		except FileNotFoundError:
			pass

		return table_data if table_data is not None else []


	def _save(self, table: str, table_data: List[dict]) -> None:
		""" Save all the items from a table """

		file_path = os.path.join(self.data_directory, table + ".json")
		os.makedirs(os.path.dirname(file_path), exist_ok = True)
		self._serializer.serialize_to_file(file_path, table_data)


	def _load_indexes(self, table: str) -> List[dict]:
		""" Load all indexes for a table """

		file_path = os.path.join(self.data_directory, "admin.json")
		administration_data = None

		try:
			administration_data = self._serializer.deserialize_from_file(file_path)
		except FileNotFoundError:
			pass

		all_indexes = administration_data["indexes"] if administration_data is not None else []
		return [ index for index in all_indexes if index["table"] == table ]


	def _match_filter(self, row: dict, filter: dict) -> bool: # pylint: disable = redefined-builtin
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

		def item_to_key(row, self, key):
			value = self._get_value(row, key)
			return value is not None, value

		for key, direction in reversed(self._normalize_order_by_expression(expression)):
			if direction in [ "asc", "ascending" ]:
				row_collection = sorted(row_collection, key = functools.partial(item_to_key, self = self, key = key), reverse = False)
			elif direction in [ "desc", "descending" ]:
				row_collection = sorted(row_collection, key = functools.partial(item_to_key, self = self, key = key), reverse = True)
		return row_collection


	def _get_value(self, row: dict, key: str) -> Any:
		""" Get a value from the item using its key """

		data = row
		for key_part in key.split("."):
			if key_part not in data.keys():
				return None
			data = data[key_part]
		return data

import glob
import json
import logging
import os

from bhamon_build_model import database_client


logger = logging.getLogger("JsonDatabaseClient")


class JsonDatabaseClient(database_client.DatabaseClient):


	def __init__(self, data_directory):
		self._data_directory = data_directory


	def find_many(self, table, filter):
		return [ row for row in self._load(table) if self._match_filter(row, filter) ]


	def find_one(self, table, filter):
		return next(( row for row in self._load(table) if self._match_filter(row, filter) ), None)


	def insert_one(self, table, data):
		all_rows = self._load(table)
		all_rows.append(data)
		self._save(table, all_rows)


	def update_one(self, table, filter, data):
		all_rows = self._load(table)
		matched_row = next(( row for row in all_rows if self._match_filter(row, filter) ), None)
		if matched_row is not None:
			matched_row.update(data)
			self._save(table, all_rows)


	def delete_one(self, table, filter):
		all_rows = self._load(table)
		matched_row = next(( row for row in all_rows if self._match_filter(row, filter) ), None)
		if matched_row is not None:
			all_rows.remove(matched_row)
			self._save(table, all_rows)


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


	def _load(self, table):
		file_path = os.path.join(self._data_directory, table + ".json")
		if not os.path.exists(file_path):
			return []
		with open(file_path) as data_file:
			return json.load(data_file)


	def _save(self, table, table_data):
		file_path = os.path.join(self._data_directory, table + ".json")
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path + ".tmp", "w") as table_data_file:
			json.dump(table_data, table_data_file, indent = 4)
		if os.path.exists(file_path):
			os.remove(file_path)
		os.rename(file_path + ".tmp", file_path)

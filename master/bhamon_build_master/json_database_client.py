import glob
import json
import os

from bhamon_build_master import database_client


class JsonDatabaseClient(database_client.DatabaseClient):


	def __init__(self, data_directory):
		self._data_directory = data_directory


	def get_all(self, table):
		return self._load(table)


	def get(self, table, key):
		return self._load(table)[key]


	def exists(self, table, key):
		return key in self._load(table)


	def create(self, table, key, data):
		table_data = self._load(table)
		table_data[key] = data
		self._save(table, table_data)


	def update(self, table, key, data):
		table_data = self._load(table)
		table_data[key] = data
		self._save(table, table_data)


	def delete(self, table, key):
		table_data = self._load(table)
		del table_data[key]
		self._save(table, table_data)


	def _load(self, table):
		file_path = os.path.join(self._data_directory, table + ".json")
		if not os.path.exists(file_path):
			return {}
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

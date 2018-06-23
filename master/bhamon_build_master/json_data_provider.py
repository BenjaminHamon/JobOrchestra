import glob
import json
import os

from bhamon_build_master import data_provider


class JsonDataProvider(data_provider.DataProvider):


	def __init__(self, data_directory, collection_name):
		self._data_directory = data_directory
		self._collection_name = collection_name


	def get(self, key):
		return self._load()[key]


	def get_all(self):
		return self._load()


	def create(self, key, data):
		collection_data = self._load()
		collection_data[key] = data
		self._save(collection_data)


	def update(self, key, data):
		collection_data = self._load()
		collection_data[key] = data
		self._save(collection_data)


	def delete(self, key):
		collection_data = self._load()
		del collection_data[key]
		self._save(collection_data)


	def _load(self):
		file_path = os.path.join(self._data_directory, self._collection_name + ".json")
		if not os.path.exists(file_path):
			return {}
		with open(file_path) as data_file:
			return json.load(data_file)


	def _save(self, data):
		file_path = os.path.join(self._data_directory, self._collection_name + ".json")
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path + ".tmp", "w") as data_file:
			json.dump(data, data_file, indent = 4)
		if os.path.exists(file_path):
			os.remove(file_path)
		os.rename(file_path + ".tmp", file_path)

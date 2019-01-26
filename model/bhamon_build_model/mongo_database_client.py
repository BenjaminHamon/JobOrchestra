import logging

from bhamon_build_model import database_client


logger = logging.getLogger("MongoDatabaseClient")


class MongoDatabaseClient(database_client.DatabaseClient):


	def __init__(self, mongo_database):
		self.mongo_database = mongo_database


	def count(self, table, filter):
		return self.mongo_database[table].count_documents(filter)


	def find_many(self, table, filter, skip = 0, limit = None):
		if limit == 0:
			return []
		if limit is None:
			limit = 0
		return list(self.mongo_database[table].find(filter, {'_id': False}, skip = skip, limit = limit))


	def find_one(self, table, filter):
		return self.mongo_database[table].find_one(filter, {'_id': False})


	def insert_one(self, table, data):
		self.mongo_database[table].insert_one(data)


	def update_one(self, table, filter, data):
		self.mongo_database[table].update_one(filter, { "$set": data })


	def delete_one(self, table, filter):
		self.mongo_database[table].delete_one(filter)

# pylint: disable = no-self-use
# pylint: disable = redefined-builtin

import logging

import pymongo

import bhamon_build_model.database_client as database_client


logger = logging.getLogger("MongoDatabaseClient")


class MongoDatabaseClient(database_client.DatabaseClient):
	""" Client for a MongoDB database. """


	def __init__(self, mongo_database):
		self.mongo_database = mongo_database


	def count(self, table, filter):
		return self.mongo_database[table].count_documents(filter)


	def find_many(self, table, filter, skip = 0, limit = None, order_by = None):
		if limit == 0:
			return []
		limit = limit if limit is not None else 0
		order_by = self._convert_order_by_expression(order_by)
		return list(self.mongo_database[table].find(filter, { "_id": False }, skip = skip, limit = limit, sort = order_by))


	def find_one(self, table, filter):
		return self.mongo_database[table].find_one(filter, { "_id": False })


	def insert_one(self, table, data):
		self.mongo_database[table].insert_one(data)
		del data["_id"]


	def update_one(self, table, filter, data):
		self.mongo_database[table].update_one(filter, { "$set": data })


	def delete_one(self, table, filter):
		self.mongo_database[table].delete_one(filter)


	def _convert_order_by_expression(self, expression):
		if expression is None:
			return None

		mongo_sort = []
		for key, direction in self._normalize_order_by_expression(expression):
			if direction in [ "asc", "ascending" ]:
				mongo_sort.append((key, pymongo.ASCENDING))
			elif direction in [ "desc", "descending" ]:
				mongo_sort.append((key, pymongo.DESCENDING))
		return mongo_sort

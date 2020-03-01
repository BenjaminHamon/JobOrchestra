import logging

from typing import List, Optional, Tuple

import pymongo

from bhamon_orchestra_model.database.database_client import DatabaseClient


logger = logging.getLogger("MongoDatabaseClient")


class MongoDatabaseClient(DatabaseClient):
	""" Client for a MongoDB database. """


	def __init__(self, mongo_client: pymongo.MongoClient) -> None:
		self.mongo_client = mongo_client


	def count(self, table: str, filter: dict) -> int: # pylint: disable = redefined-builtin
		""" Return how many items are in a table, after applying a filter """
		return self.mongo_client.get_database()[table].count_documents(filter)


	def find_many(self, # pylint: disable = too-many-arguments
			table: str, filter: dict, # pylint: disable = redefined-builtin
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[Tuple[str,str]] = None) -> List[dict]:
		""" Return a list of items from a table, after applying a filter, with options for limiting and sorting results """

		if limit == 0:
			return []

		limit = limit if limit is not None else 0
		order_by = self._convert_order_by_expression(order_by)
		return list(self.mongo_client.get_database()[table].find(filter, { "_id": False }, skip = skip, limit = limit, sort = order_by))


	def find_one(self, table: str, filter: dict) -> Optional[dict]: # pylint: disable = redefined-builtin
		""" Return a single item (or nothing) from a table, after applying a filter """
		return self.mongo_client.get_database()[table].find_one(filter, { "_id": False })


	def insert_one(self, table: str, data: dict) -> dict:
		""" Insert a new item into a table """
		self.mongo_client.get_database()[table].insert_one(data)
		del data["_id"]


	def update_one(self, table: str, filter: dict, data: dict) -> None: # pylint: disable = redefined-builtin
		""" Update a single item (or nothing) from a table, after applying a filter """
		self.mongo_client.get_database()[table].update_one(filter, { "$set": data })


	def delete_one(self, table: str, filter: dict) -> None: # pylint: disable = redefined-builtin
		""" Delete a single item (or nothing) from a table, after applying a filter """
		self.mongo_client.get_database()[table].delete_one(filter)


	def close(self) -> None:
		self.mongo_client.close()


	def _convert_order_by_expression(self, expression: Optional[List[Tuple[str,str]]]) -> Optional[List[Tuple[str,int]]]:
		""" Convert a order-by expression to its pymongo representation """

		if expression is None:
			return None

		mongo_sort = []
		for key, direction in self._normalize_order_by_expression(expression):
			if direction in [ "asc", "ascending" ]:
				mongo_sort.append((key, pymongo.ASCENDING))
			elif direction in [ "desc", "descending" ]:
				mongo_sort.append((key, pymongo.DESCENDING))
		return mongo_sort

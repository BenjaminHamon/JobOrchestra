import abc
from typing import List, Optional, Tuple


class DatabaseClient(abc.ABC):
	""" Base class for a database client """


	def __enter__(self):
		return self


	def __exit__(self, exception_type, exception_value, traceback):
		self.close()


	@abc.abstractmethod
	def count(self, table: str, filter: dict) -> int: # pylint: disable = redefined-builtin
		""" Return how many items are in a table, after applying a filter """


	@abc.abstractmethod
	def find_many(self, # pylint: disable = too-many-arguments
			table: str, filter: dict, # pylint: disable = redefined-builtin
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[List[Tuple[str,str]]] = None) -> List[dict]:
		""" Return a list of items from a table, after applying a filter, with options for limiting and sorting results """


	@abc.abstractmethod
	def find_one(self, table: str, filter: dict) -> Optional[dict]: # pylint: disable = redefined-builtin
		""" Return a single item (or nothing) from a table, after applying a filter """


	@abc.abstractmethod
	def insert_one(self, table: str, data: dict) -> None:
		""" Insert a new item into a table """


	@abc.abstractmethod
	def insert_many(self, table: str, dataset: List[dict]) -> None:
		""" Insert a list of items into a table """


	@abc.abstractmethod
	def update_one(self, table: str, filter: dict, data: dict) -> None: # pylint: disable = redefined-builtin
		""" Update a single item (or nothing) from a table, after applying a filter """


	@abc.abstractmethod
	def delete_one(self, table: str, filter: dict) -> None: # pylint: disable = redefined-builtin
		""" Delete a single item (or nothing) from a table, after applying a filter """


	@abc.abstractmethod
	def close(self) -> None:
		""" Close the database connection """


	def _normalize_order_by_expression(self, expression: Optional[List[Tuple[str,str]]]) -> Optional[List[Tuple[str,str]]]:
		""" Normalize an order-by expression to simplify its interpretation """

		if expression is None:
			return None

		normalized_expression = []
		for item in expression:
			if isinstance(item, str):
				normalized_expression.append((item, "ascending"))
			elif len(item) == 1:
				normalized_expression.append((item[0], "ascending"))
			elif len(item) == 2:
				if item[1] not in [ "asc", "ascending", "desc", "descending" ]:
					raise ValueError("Invalid order_by direction '%s'" % item[1])
				normalized_expression.append(item)
			else:
				raise ValueError("Invalid order_by item '%s'" % str(item))
		return normalized_expression

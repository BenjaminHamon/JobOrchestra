# pylint: disable = no-self-use
# pylint: disable = redefined-builtin

import abc

class DatabaseClient(abc.ABC):

	@abc.abstractmethod
	def count(self, table, filter):
		pass

	@abc.abstractmethod
	def find_many(self, table, filter, skip = 0, limit = None, order_by = None):
		pass

	@abc.abstractmethod
	def find_one(self, table, filter):
		pass

	@abc.abstractmethod
	def insert_one(self, table, data):
		pass

	@abc.abstractmethod
	def update_one(self, table, filter, data):
		pass

	@abc.abstractmethod
	def delete_one(self, table, filter):
		pass

	def _normalize_order_by_expression(self, expression):
		if expression is None:
			return None
		normalized_expression = []
		for tuple in expression:
			if len(tuple) == 1:
				normalized_expression.append((tuple[0], "ascending"))
			elif len(tuple) == 2:
				if tuple[1] not in [ "asc", "ascending", "desc", "descending" ]:
					raise ValueError("Invalid order_by direction '%s'" % tuple[1])
				normalized_expression.append(tuple)
			else:
				raise ValueError("Invalid order_by item '%s'" % str(tuple))
		return normalized_expression

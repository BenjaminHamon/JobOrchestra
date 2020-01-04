import abc

class DatabaseClient(abc.ABC):

	@abc.abstractmethod
	def count(self, table, filter): # pylint: disable = redefined-builtin
		pass

	@abc.abstractmethod
	def find_many( # pylint: disable = too-many-arguments
			self, table, filter, skip = 0, limit = None, order_by = None): # pylint: disable = redefined-builtin
		pass

	@abc.abstractmethod
	def find_one(self, table, filter): # pylint: disable = redefined-builtin
		pass

	@abc.abstractmethod
	def insert_one(self, table, data):
		pass

	@abc.abstractmethod
	def update_one(self, table, filter, data): # pylint: disable = redefined-builtin
		pass

	@abc.abstractmethod
	def delete_one(self, table, filter): # pylint: disable = redefined-builtin
		pass

	def _normalize_order_by_expression(self, expression): # pylint: disable = no-self-use
		if expression is None:
			return None
		normalized_expression = []
		for item in expression:
			if len(item) == 1:
				normalized_expression.append((item[0], "ascending"))
			elif len(item) == 2:
				if item[1] not in [ "asc", "ascending", "desc", "descending" ]:
					raise ValueError("Invalid order_by direction '%s'" % item[1])
				normalized_expression.append(item)
			else:
				raise ValueError("Invalid order_by item '%s'" % str(item))
		return normalized_expression

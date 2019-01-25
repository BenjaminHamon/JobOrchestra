import abc

class DatabaseClient(abc.ABC):

	@abc.abstractmethod
	def find_many(self, table, filter):
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

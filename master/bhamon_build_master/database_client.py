import abc

class DatabaseClient(abc.ABC):

	@abc.abstractmethod
	def get_all(self, table):
		pass

	@abc.abstractmethod
	def get(self, table, key):
		pass

	@abc.abstractmethod
	def exists(self, table, key):
		pass

	@abc.abstractmethod
	def create(self, table, key, data):
		pass

	@abc.abstractmethod
	def update(self, table, key, data):
		pass

	@abc.abstractmethod
	def delete(self, table, key):
		pass

import abc

class DataProvider(abc.ABC):

	@abc.abstractmethod
	def get_all(self):
		pass

	@abc.abstractmethod
	def get(self, key):
		pass

	@abc.abstractmethod
	def exists(self, key):
		pass

	@abc.abstractmethod
	def create(self, key, data):
		pass

	@abc.abstractmethod
	def update(self, key, data):
		pass

	@abc.abstractmethod
	def delete(self, key):
		pass

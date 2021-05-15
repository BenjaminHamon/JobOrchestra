import abc


class Service(abc.ABC):


	@abc.abstractmethod
	def get_definition(self) -> dict:
		pass


	@abc.abstractmethod
	def get_status(self) -> dict:
		pass

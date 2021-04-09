import abc


class DatabaseAdministration(abc.ABC):
	""" Base class for a database client """


	def __enter__(self):
		return self


	def __exit__(self, exception_type, exception_value, traceback):
		self.close()


	@abc.abstractmethod
	def initialize(self, simulate: bool = False) -> None:
		""" Initialize the database """


	@abc.abstractmethod
	def upgrade(self, simulate: bool = False) -> None:
		""" Upgrade the database """


	@abc.abstractmethod
	def close(self) -> None:
		""" Close the database connection """

import abc
from typing import Optional


class DatabaseAdministration(abc.ABC):
	""" Base class for a database client """


	def __enter__(self):
		return self


	def __exit__(self, exception_type, exception_value, traceback):
		self.close()


	@abc.abstractmethod
	def get_metadata(self) -> dict:
		""" Retrieve the database metadata """


	@abc.abstractmethod
	def initialize(self, # pylint: disable = too-many-arguments
			product: Optional[str] = None,
			copyright: Optional[str] = None, # pylint: disable = redefined-builtin
			version: Optional[str] = None,
			date: Optional[str] = None,
			simulate: bool = False) -> None:
		""" Initialize the database """


	@abc.abstractmethod
	def upgrade(self, target_version: Optional[str] = None, simulate: bool = False) -> None:
		""" Upgrade the database """


	@abc.abstractmethod
	def close(self) -> None:
		""" Close the database connection """

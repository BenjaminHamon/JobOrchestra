import abc
import contextlib
from typing import Any, List, Optional


class DataStorage(abc.ABC):
	""" Base class for a data storage """


	@abc.abstractmethod
	def get_keys(self) -> List[str]:
		""" Get all keys """


	@abc.abstractmethod
	def exists(self, key: str) -> bool:
		""" Return a boolean indicating if the provided key is present """


	@abc.abstractmethod
	def get_size(self, key: str) -> int:
		""" Return the size of the data stored for the provided key """


	@abc.abstractmethod
	def get(self, key: str) -> Optional[Any]:
		""" Get the data for the provided key """


	@abc.abstractmethod
	def get_chunk(self, key: str, skip: int = 0, limit: Optional[int] = None) -> Optional[Any]:
		""" Get a data chunk for the provided key """


	@abc.abstractmethod
	def set(self, key: str, data: Any) -> None:
		""" Set the data for the provided key """


	@abc.abstractmethod
	def append(self, key: str, data: Any) -> None:
		""" Append a data chunk for the provided key """


	@abc.abstractmethod
	def delete(self, key: str) -> None:
		""" Delete the data for the provided key """


	@abc.abstractmethod
	@contextlib.contextmanager
	def lock(self, key: str, timeout = 5) -> None:
		""" Lock for the provided key """

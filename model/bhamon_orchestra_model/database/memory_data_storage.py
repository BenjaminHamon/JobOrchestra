import contextlib
import logging
from typing import Any, List, Optional

from bhamon_orchestra_model.database.data_storage import DataStorage


logger = logging.getLogger("MemoryDataStorage")


class MemoryDataStorage(DataStorage):
	""" Data storage using the memory """


	def __init__(self) -> None:
		self.storage = {}


	def get_keys(self) -> List[str]:
		""" Get all keys """

		return list(self.storage.keys())


	def exists(self, key: str) -> bool:
		""" Return a boolean indicating if the provided key is present """

		return key in self.storage


	def get_size(self, key: str) -> int:
		""" Return the size of the data stored for the provided key """

		try:
			return len(self.storage[key])
		except KeyError:
			return 0


	def get(self, key: str) -> Optional[Any]:
		""" Get the data for the provided key """

		return self.storage.get(key, None)


	def get_chunk(self, key: str, skip: int = 0, limit: Optional[int] = None) -> Optional[Any]:
		""" Get a data chunk for the provided key """

		data = self.storage.get(key, None)
		if data is None:
			return None

		start_index = skip
		end_index = (skip + limit) if limit is not None else None
		return data [ start_index : end_index ]


	def set(self, key: str, data: Any) -> None:
		""" Set the data for the provided key """

		self.storage[key] = data


	def append(self, key: str, data: Any) -> None:
		""" Append data for the provided key """

		self.storage[key] += data


	def delete(self, key: str) -> None:
		""" Delete the data for the provided key """

		try:
			del self.storage[key]
		except KeyError:
			pass


	@contextlib.contextmanager
	def lock(self, key: str, timeout = 5) -> None:
		""" Lock for the provided key """

		raise NotImplementedError

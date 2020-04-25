import logging

from typing import Optional, Tuple


logger = logging.getLogger("MemoryFileStorage")


class MemoryFileStorage:
	""" Client for a file storage in memory, intended for development only. """


	def __init__(self) -> None:
		self.storage = {}


	def exists(self, file_path: str) -> bool:
		return file_path in self.storage


	def get_universal_size(self, file_path: str) -> int:
		return len(self.storage[file_path])


	def load_or_default(self, file_path: str, default_value: Optional[str] = None) -> Optional[str]:
		return self.storage.get(file_path, default_value)


	def load(self, file_path: str) -> str:
		return self.storage[file_path]


	def load_chunk_or_default(self, file_path: str, default_value: Optional[str] = None, skip: int = 0, limit: Optional[int] = None) -> Tuple[Optional[str], int]:
		try:
			return self.load_chunk(file_path, skip = skip, limit = limit)
		except KeyError:
			return default_value, 0


	def load_chunk(self, file_path: str, skip: int = 0, limit: Optional[int] = None) -> Tuple[str, int]:
		start_index = skip
		end_index = (skip + limit) if limit is not None else None
		result = self.storage[file_path][ start_index : end_index ]
		return result, len(result)


	def save(self, file_path: str, data: str) -> None:
		self.storage[file_path] = data


	def append_unsafe(self, file_path: str, data: str) -> None:
		self.storage[file_path] = self.storage.get(file_path, "") + data


	def delete(self, file_path: str) -> None:
		del self.storage[file_path]

import os

from typing import Optional, Tuple


class FileStorage:


	def __init__(self, data_directory: str) -> None:
		self._data_directory = data_directory


	def exists(self, file_path: str) -> bool:
		file_path = os.path.join(self._data_directory, file_path)
		return os.path.isfile(file_path)


	def get_universal_size(self, file_path: str) -> int:
		"""
		Return the actual content size once loaded rather than the size of the file itself,
		which can change because of newline characters being translated.
		"""
		return len(self.load(file_path))


	def load_or_default(self, file_path: str, default_value: Optional[str] = None) -> Optional[str]:
		try:
			return self.load(file_path)
		except OSError:
			return default_value


	def load(self, file_path: str) -> str:
		file_path = os.path.join(self._data_directory, file_path)
		with open(file_path, mode = "r", encoding = "utf-8") as data_file:
			return data_file.read()


	def load_chunk_or_default(self, file_path: str, default_value: Optional[str] = None, skip: int = 0, limit: Optional[int] = None) -> Tuple[Optional[str], int]:
		try:
			return self.load_chunk(file_path, skip = skip, limit = limit)
		except OSError:
			return default_value, 0


	def load_chunk(self, file_path: str, skip: int = 0, limit: Optional[int] = None) -> Tuple[str, int]:
		file_path = os.path.join(self._data_directory, file_path)
		with open(file_path, mode = "r", encoding = "utf-8") as data_file:
			data_file.seek(skip)
			return data_file.read(limit), data_file.tell()


	def save(self, file_path: str, data: str) -> None:
		file_path = os.path.join(self._data_directory, file_path)
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path + ".tmp", mode = "w", encoding = "utf-8") as data_file:
			data_file.write(data)
		os.replace(file_path + ".tmp", file_path)


	def append_unsafe(self, file_path: str, data: str) -> None:
		file_path = os.path.join(self._data_directory, file_path)
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path, mode = "a", encoding = "utf-8") as data_file:
			data_file.write(data)


	def delete(self, file_path: str) -> None:
		file_path = os.path.join(self._data_directory, file_path)
		os.remove(file_path)

import contextlib
import glob
import logging
import os
from typing import Any, List, Optional, Union

import filelock

from bhamon_orchestra_model.database.data_storage import DataStorage


logger = logging.getLogger("FileDataStorage")


class FileDataStorage(DataStorage):
	""" Data storage using the file system """


	def __init__(self, storage_directory) -> None:
		self.storage_directory = storage_directory


	def get_keys(self, prefix: str) -> List[str]:
		""" Get all keys """

		all_keys = []
		for file_path in glob.glob(self.get_file_path(prefix + "**"), recursive = True):
			if os.path.isfile(file_path):
				all_keys.append(os.path.relpath(file_path, self.storage_directory).replace("\\", "/"))
		return all_keys


	def get_file_path(self, key: str) -> str:
		return os.path.normpath(os.path.join(self.storage_directory, key))


	def exists(self, key: str) -> bool:
		""" Return a boolean indicating if the provided key is present """

		return os.path.isfile(self.get_file_path(key))


	def get_size(self, key: str) -> int:
		""" Return the size of the data stored for the provided key """

		try:
			return os.path.getsize(self.get_file_path(key))
		except FileNotFoundError:
			return 0


	def get(self, key: str) -> Optional[Any]:
		""" Get the data for the provided key """

		try:
			with open(self.get_file_path(key), mode = "rb") as data_file:
				return data_file.read()
		except FileNotFoundError:
			return None


	def get_chunk(self, key: str, skip: int = 0, limit: Optional[int] = None) -> Optional[Any]:
		""" Get a data chunk for the provided key """

		try:
			with open(self.get_file_path(key), mode = "rb") as data_file:
				data_file.seek(skip)
				return data_file.read(limit)
		except FileNotFoundError:
			return None


	def set(self, key: str, data: Any) -> None:
		""" Set the data for the provided key """

		file_path = self.get_file_path(key)
		os.makedirs(os.path.dirname(file_path), exist_ok = True)
		with open(file_path + ".tmp", mode = "wb") as data_file:
			data_file.write(data)
		os.replace(file_path + ".tmp", file_path)


	def append(self, key: str, data: Any) -> None:
		""" Append data for the provided key """

		file_path = self.get_file_path(key)
		os.makedirs(os.path.dirname(file_path), exist_ok = True)
		with open(file_path, mode = "ab") as data_file:
			data_file.write(data)


	def delete(self, key: str) -> None:
		""" Delete the data for the provided key """

		try:
			os.remove(self.get_file_path(key))
		except FileNotFoundError:
			pass


	@contextlib.contextmanager
	def lock(self, key: str, timeout: Union[int,float] = 5) -> None:
		""" Lock for the provided key """

		with filelock.FileLock(self.get_file_path(key) + ".lock", timeout = timeout):
			yield

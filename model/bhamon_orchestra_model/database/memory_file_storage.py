import logging


logger = logging.getLogger("MemoryFileStorage")


class MemoryFileStorage:
	""" Client for a file storage in memory, intended for development only. """


	def __init__(self):
		self.storage = {}


	def exists(self, file_path):
		return file_path in self.storage


	def get_size(self, file_path):
		return len(self.storage[file_path])


	def load_or_default(self, file_path, default_value = None):
		return self.storage.get(file_path, default_value)


	def load(self, file_path):
		return self.storage[file_path]


	def load_chunk_or_default(self, file_path, default_value = None, skip = 0, limit = None):
		try:
			return self.load_chunk(file_path, skip = skip, limit = limit)
		except KeyError:
			return default_value


	def load_chunk(self, file_path, skip = 0, limit = None):
		start_index = skip
		end_index = (skip + limit) if limit is not None else None
		return self.storage[file_path][ start_index : end_index ]


	def save(self, file_path, data):
		self.storage[file_path] = data


	def append_unsafe(self, file_path, data):
		self.storage[file_path] = self.storage.get(file_path, "") + data


	def delete(self, file_path):
		del self.storage[file_path]

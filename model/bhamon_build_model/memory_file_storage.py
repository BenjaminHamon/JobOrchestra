import logging


logger = logging.getLogger("MemoryFileStorage")


class MemoryFileStorage:
	""" Client for a file storage in memory, intended for development only. """


	def __init__(self):
		self.storage = {}


	def exists(self, file_path):
		return file_path in self.storage


	def load(self, file_path):
		return self.storage.get(file_path, "")


	def save(self, file_path, data):
		self.storage[file_path] = data

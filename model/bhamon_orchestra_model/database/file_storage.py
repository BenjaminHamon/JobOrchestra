import os


class FileStorage:


	def __init__(self, data_directory):
		self._data_directory = data_directory


	def exists(self, file_path):
		file_path = os.path.join(self._data_directory, file_path)
		return os.path.isfile(file_path)


	def get_size(self, file_path):
		file_path = os.path.join(self._data_directory, file_path)
		return os.path.getsize(file_path)


	def load_or_default(self, file_path, default_value = None):
		try:
			return self.load(file_path)
		except OSError:
			return default_value


	def load(self, file_path):
		file_path = os.path.join(self._data_directory, file_path)
		with open(file_path, mode = "r") as data_file:
			return data_file.read()


	def load_chunk_or_default(self, file_path, default_value = None, skip = 0, limit = None):
		try:
			return self.load_chunk(file_path, skip = skip, limit = limit)
		except OSError:
			return default_value, 0


	def load_chunk(self, file_path, skip = 0, limit = None):
		file_path = os.path.join(self._data_directory, file_path)
		with open(file_path, mode = "r") as data_file:
			data_file.seek(skip)
			return data_file.read(limit), data_file.tell()


	def save(self, file_path, data):
		file_path = os.path.join(self._data_directory, file_path)
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path + ".tmp", mode = "w") as data_file:
			data_file.write(data)
		os.replace(file_path + ".tmp", file_path)


	def append_unsafe(self, file_path, data):
		file_path = os.path.join(self._data_directory, file_path)
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path, mode = "a") as data_file:
			data_file.write(data)


	def delete(self, file_path):
		file_path = os.path.join(self._data_directory, file_path)
		os.remove(file_path)

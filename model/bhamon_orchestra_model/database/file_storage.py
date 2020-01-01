import os


class FileStorage:


	def __init__(self, data_directory):
		self._data_directory = data_directory


	def exists(self, file_path):
		file_path = os.path.join(self._data_directory, file_path)
		return os.path.isfile(file_path)


	def load(self, file_path):
		file_path = os.path.join(self._data_directory, file_path)
		if not os.path.exists(file_path):
			return ""
		with open(file_path) as data_file:
			return data_file.read()


	def save(self, file_path, data):
		file_path = os.path.join(self._data_directory, file_path)
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path + ".tmp", "w") as data_file:
			data_file.write(data)
		os.replace(file_path + ".tmp", file_path)

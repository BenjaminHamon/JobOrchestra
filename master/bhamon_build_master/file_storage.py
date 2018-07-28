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
		with open(file_path) as log_file:
			return log_file.read()


	def save(self, file_path, data):
		file_path = os.path.join(self._data_directory, file_path)
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path + ".tmp", "w") as log_file:
			log_file.write(data)
		if os.path.exists(file_path):
			os.remove(file_path)
		os.rename(file_path + ".tmp", file_path)

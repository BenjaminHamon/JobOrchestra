import logging


logger = logging.getLogger("JsonDatabaseAdministration")


class JsonDatabaseAdministration:
	""" Administration client for a database storing data as json files, intended for development only. """


	def __init__(self, data_directory: str) -> None:
		self._data_directory = data_directory


	def initialize(self, simulate: bool = False) -> None:
		logger.info("Initializing (Path: '%s')" + (" (simulation)" if simulate else ""), self._data_directory) # pylint: disable = logging-not-lazy


	def upgrade(self, simulate: bool = False) -> None:
		raise NotImplementedError("Upgrading a JSON database is not supported")

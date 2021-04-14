import logging
import os
from typing import List, Optional, Tuple

import bhamon_orchestra_model
from bhamon_orchestra_model.database.database_administration import DatabaseAdministration
from bhamon_orchestra_model.serialization.serializer import Serializer


logger = logging.getLogger("JsonDatabaseAdministration")


class JsonDatabaseAdministration(DatabaseAdministration):
	""" Administration client for a database storing data as json files, intended for development only. """


	def __init__(self, serializer: Serializer, data_directory: str) -> None:
		self._serializer = serializer
		self.data_directory = data_directory


	def __enter__(self):
		return self


	def __exit__(self, exception_type, exception_value, traceback):
		self.close()


	def get_metadata(self) -> dict:
		return self._load()["metadata"]


	def initialize(self, # pylint: disable = too-many-arguments
			product: Optional[str] = None,
			copyright: Optional[str] = None, # pylint: disable = redefined-builtin
			version: Optional[str] = None,
			date: Optional[str] = None,
			simulate: bool = False) -> None:

		logger.info("Initializing (Path: '%s')" + (" (simulation)" if simulate else ""), self.data_directory) # pylint: disable = logging-not-lazy

		if self.get_metadata() is not None:
			raise RuntimeError("Database is already initialized")

		metadata = {
			"product": product if product is not None else bhamon_orchestra_model.__product__,
			"copyright": copyright if copyright is not None else bhamon_orchestra_model.__copyright__,
			"version": version if version is not None else bhamon_orchestra_model.__version__,
			"date": date if date is not None else bhamon_orchestra_model.__date__,
		}

		logger.info("Creating admin data")
		administration_data = { "metadata": metadata, "indexes": [] }
		if not simulate:
			self._save(administration_data)

		logger.info("Creating run index")
		if not simulate:
			self.create_index("run", "identifier_unique", [ ("project", "ascending"), ("identifier", "ascending") ], is_unique = True)

		logger.info("Creating job index")
		if not simulate:
			self.create_index("job", "identifier_unique", [ ("project", "ascending"), ("identifier", "ascending") ], is_unique = True)

		logger.info("Creating schedule index")
		if not simulate:
			self.create_index("schedule", "identifier_unique", [ ("project", "ascending"), ("identifier", "ascending") ], is_unique = True)

		logger.info("Creating user index")
		if not simulate:
			self.create_index("user", "identifier_unique", [ ("identifier", "ascending") ], is_unique = True)

		logger.info("Creating worker index")
		if not simulate:
			self.create_index("worker", "identifier_unique", [ ("identifier", "ascending") ], is_unique = True)


	def upgrade(self, target_version: Optional[str] = None, simulate: bool = False) -> None:
		raise NotImplementedError("Upgrading a JSON database is not supported")


	def create_index(self, table: str, identifier: str, field_collection: List[Tuple[str,str]], is_unique: bool = False) -> None:
		field_collection = [ field for field, direction in field_collection ]

		administration_data = self._load()

		existing_index = next(( index for index in administration_data["indexes"] if index["table"] == table and index["identifier"] == identifier ), None)
		if existing_index is not None:
			raise ValueError("Index '%s' already exists for table '%s'" % (identifier, table))

		administration_data["indexes"].append(
			{
				"table": table,
				"identifier": identifier,
				"field_collection": field_collection,
				"is_unique": is_unique,
			}
		)

		self._save(administration_data)


	def close(self) -> None:
		pass


	def _load(self) -> dict:
		file_path = os.path.join(self.data_directory, "admin.json")
		administration_data = None

		try:
			administration_data = self._serializer.deserialize_from_file(file_path)
		except FileNotFoundError:
			pass

		if administration_data is None:
			administration_data = {
				"metadata": None,
				"indexes": [],
			}

		if administration_data["metadata"] is not None:
			administration_data["metadata"]["date"] = administration_data["metadata"]["date"].replace(tzinfo = None).isoformat() + "Z"

		return administration_data


	def _save(self, administration_data: dict) -> None:
		file_path = os.path.join(self.data_directory, "admin.json")
		os.makedirs(os.path.dirname(file_path), exist_ok = True)
		self._serializer.serialize_to_file(file_path, administration_data)

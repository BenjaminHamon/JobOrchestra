import io
import logging
import os
import time
import uuid
import zipfile

from typing import List, Optional, Tuple

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.database.data_storage import DataStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.serialization.serializer import Serializer


logger = logging.getLogger("RunProvider")


class RunProvider:


	def __init__(self, data_storage: DataStorage, date_time_provider: DateTimeProvider) -> None:
		self.data_storage = data_storage
		self.date_time_provider = date_time_provider
		self.table = "run"


	def count(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: Optional[str] = None, job: Optional[str] = None, worker: Optional[str] = None, status: Optional[str] = None) -> int:

		filter = { "project": project, "job": job, "worker": worker, "status": status } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return database_client.count(self.table, filter)


	def get_list(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: Optional[str] = None, job: Optional[str] = None, worker: Optional[str] = None, status: Optional[str] = None,
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[List[Tuple[str,str]]] = None) -> List[dict]:

		filter = { "project": project, "job": job, "worker": worker, "status": status } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		run_collection = database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)
		return [ self.convert_to_public(run) for run in run_collection ]


	def get_list_as_documents(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: Optional[str] = None, job: Optional[str] = None, worker: Optional[str] = None, status: Optional[str] = None,
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[List[Tuple[str,str]]] = None) -> List[dict]:

		filter = { "project": project, "job": job, "worker": worker, "status": status } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, database_client: DatabaseClient, project: str, run_identifier: str) -> Optional[dict]:
		run = database_client.find_one(self.table, { "project": project, "identifier": run_identifier })
		return self.convert_to_public(run) if run is not None else None


	def create_identifier(self, database_client: DatabaseClient) -> str: # pylint: disable = unused-argument
		return str(uuid.uuid4())


	def create(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: str, job: str, parameters: dict, source: dict) -> dict:

		identifier = self.create_identifier(database_client)
		now = self.date_time_provider.now()

		run = {
			"identifier": identifier,
			"project": project,
			"job": job,
			"parameters": parameters,
			"source": source,
			"worker": None,
			"status": "pending",
			"start_date": None,
			"completion_date": None,
			"results": None,
			"should_cancel": False,
			"should_abort": False,
			"creation_date": now,
			"update_date": now,
		}

		database_client.insert_one(self.table, run)
		return run


	def update_status(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			run: dict, worker: Optional[str] = None, status: Optional[str] = None,
			start_date: Optional[str] = None, completion_date: Optional[str] = None,
			should_cancel: Optional[bool] = None, should_abort: Optional[bool] = None) -> None:

		now = self.date_time_provider.now()

		update_data = {
			"worker": worker,
			"status": status,
			"start_date": start_date,
			"completion_date": completion_date,
			"should_cancel": should_cancel,
			"should_abort": should_abort,
			"update_date": now,
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		run.update(update_data)
		database_client.update_one(self.table, { "project": run["project"], "identifier": run["identifier"] }, update_data)


	def get_log(self, project: str, run_identifier: str) -> Tuple[str,int]: # pylint: disable = unused-argument
		key = "projects/{project}/runs/{run_identifier}/run.log".format(**locals())
		raw_data = self.data_storage.get(key)
		text_data = raw_data.decode("utf-8").replace(os.linesep, "\n") if raw_data is not None else ""
		return text_data, len(raw_data) if raw_data is not None else 0


	def get_log_chunk(self, project: str, run_identifier: str, skip: int = 0, limit: Optional[int] = None) -> Tuple[str,int]: # pylint: disable = unused-argument
		key = "projects/{project}/runs/{run_identifier}/run.log".format(**locals())
		raw_data = self.data_storage.get_chunk(key, skip = skip, limit = limit)
		text_data = raw_data.decode("utf-8").replace(os.linesep, "\n") if raw_data is not None else ""
		return text_data, (len(raw_data) if raw_data is not None else 0) + skip


	def append_log_chunk(self, project: str, run_identifier: str, log_chunk: str) -> None: # pylint: disable = unused-argument
		key = "projects/{project}/runs/{run_identifier}/run.log".format(**locals())
		self.data_storage.append(key, log_chunk.replace("\n", os.linesep).encode("utf-8"))


	def get_results(self, database_client: DatabaseClient, project: str, run_identifier: str) -> dict:
		return database_client.find_one(self.table, { "project": project, "identifier": run_identifier })["results"]


	def set_results(self, database_client: DatabaseClient, run: dict, results: dict) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"results": results,
			"update_date": now,
		}

		run.update(update_data)
		database_client.update_one(self.table, { "project": run["project"], "identifier": run["identifier"] }, update_data)


	def get_archive(self, database_client: DatabaseClient, serializer: Serializer, project: str, run_identifier: str) -> dict:
		run = database_client.find_one(self.table, { "project": project, "identifier": run_identifier })
		if run is None:
			return None

		file_name = run_identifier + ".zip"
		now = time.gmtime()

		with io.BytesIO() as file_object:
			with zipfile.ZipFile(file_object, mode = "w", compression = zipfile.ZIP_DEFLATED) as archive:
				entry_info = zipfile.ZipInfo("run" + serializer.get_file_extension(), now[0:6])
				entry_info.external_attr = 0o644 << 16
				archive.writestr(entry_info, serializer.serialize_to_string(run))

				entry_info = zipfile.ZipInfo("run.log", now[0:6])
				entry_info.external_attr = 0o644 << 16
				archive.writestr(entry_info, self.get_log(project, run_identifier)[0])

			return { "file_name": file_name, "data": file_object.getvalue(), "type": "zip" }


	def convert_to_public(self, run: dict) -> dict:
		keys_to_return = [
			"identifier", "project", "job", "worker", "parameters", "source", "status",
			"start_date", "completion_date", "should_cancel", "should_abort", "creation_date", "update_date",
		]

		return { key: value for key, value in run.items() if key in keys_to_return }

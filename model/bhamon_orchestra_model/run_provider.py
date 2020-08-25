import io
import json
import logging
import os
import time
import uuid
import zipfile

from typing import List, Optional, Tuple

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.database.file_storage import FileStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider


logger = logging.getLogger("RunProvider")


class RunProvider:


	def __init__(self, file_storage: FileStorage, date_time_provider: DateTimeProvider) -> None:
		self.file_storage = file_storage
		self.date_time_provider = date_time_provider
		self.table = "run"


	def count(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: Optional[str] = None, job: Optional[str] = None, worker: Optional[str] = None, status: Optional[str] = None) -> int:

		filter = { "project": project, "job": job, "worker": worker, "status": status } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return database_client.count(self.table, filter)


	def get_list(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: Optional[str] = None, job: Optional[str] = None, worker: Optional[str] = None, status: Optional[str] = None,
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[Tuple[str,str]] = None) -> List[dict]:

		filter = { "project": project, "job": job, "worker": worker, "status": status } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		run_collection = database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)
		return [ self.convert_to_public(run) for run in run_collection ]


	def get_list_as_documents(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: Optional[str] = None, job: Optional[str] = None, worker: Optional[str] = None, status: Optional[str] = None,
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[Tuple[str,str]] = None) -> List[dict]:

		filter = { "project": project, "job": job, "worker": worker, "status": status } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, database_client: DatabaseClient, project: str, run_identifier: str) -> Optional[dict]:
		run = database_client.find_one(self.table, { "project": project, "identifier": run_identifier })
		return self.convert_to_public(run) if run is not None else None


	def create(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: str, job: str, parameters: dict, source: dict) -> dict:
		now = self.date_time_provider.now()

		run = {
			"identifier": str(uuid.uuid4()),
			"project": project,
			"job": job,
			"parameters": parameters,
			"source": source,
			"status": "pending",
			"worker": None,
			"creation_date": self.date_time_provider.serialize(now),
			"update_date": self.date_time_provider.serialize(now),
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
			"update_date": self.date_time_provider.serialize(now),
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		run.update(update_data)
		database_client.update_one(self.table, { "project": run["project"], "identifier": run["identifier"] }, update_data)


	def get_all_steps(self, database_client: DatabaseClient, project: str, run_identifier: str) -> List[dict]:
		return database_client.find_one(self.table, { "project": project, "identifier": run_identifier }).get("steps", [])


	def get_step(self, database_client: DatabaseClient, project: str, run_identifier: str, step_index: int) -> dict:
		return database_client.find_one(self.table, { "project": project, "identifier": run_identifier })["steps"][step_index]


	def update_steps(self, database_client: DatabaseClient, run: dict, step_collection: List[dict]) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"steps": step_collection,
			"update_date": self.date_time_provider.serialize(now),
		}

		run.update(update_data)
		database_client.update_one(self.table, { "project": run["project"], "identifier": run["identifier"] }, update_data)


	def _get_step_log_path(self, database_client: DatabaseClient, project: str, run_identifier: str, step_index: int) -> str:
		run_step = self.get_step(database_client, project, run_identifier, step_index)
		return os.path.join("projects", project, "runs", run_identifier, "step_{index}_{name}.log".format(**run_step))


	def has_step_log(self, database_client: DatabaseClient, project: str, run_identifier: str, step_index: int) -> bool:
		return self.file_storage.exists(self._get_step_log_path(database_client, project, run_identifier, step_index))


	def get_step_log(self, database_client: DatabaseClient, project: str, run_identifier: str, step_index: int) -> Tuple[str,int]:
		return self.file_storage.load_chunk_or_default(self._get_step_log_path(database_client, project, run_identifier, step_index), "", skip = 0, limit = None)


	def get_step_log_chunk(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: str, run_identifier: str, step_index: int, skip: int = 0, limit: Optional[int] = None) -> Tuple[str,int]:
		return self.file_storage.load_chunk_or_default(self._get_step_log_path(database_client, project, run_identifier, step_index), "", skip = skip, limit = limit)


	def get_step_log_size(self, database_client: DatabaseClient, project: str, run_identifier: str, step_index: int) -> int:
		return self.file_storage.get_universal_size(self._get_step_log_path(database_client, project, run_identifier, step_index))


	def append_step_log(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			project: str, run_identifier: str, step_index: int, log_text: str) -> None:
		self.file_storage.append_unsafe(self._get_step_log_path(database_client, project, run_identifier, step_index), log_text)


	def delete_step_log(self, database_client: DatabaseClient, project: str, run_identifier: str, step_index: int) -> None:
		self.file_storage.delete(self._get_step_log_path(database_client, project, run_identifier, step_index))


	def get_results(self, database_client: DatabaseClient, project: str, run_identifier: str) -> dict:
		return database_client.find_one(self.table, { "project": project, "identifier": run_identifier }).get("results", {})


	def set_results(self, database_client: DatabaseClient, run: dict, results: dict) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"results": results,
			"update_date": self.date_time_provider.serialize(now),
		}

		run.update(update_data)
		database_client.update_one(self.table, { "project": run["project"], "identifier": run["identifier"] }, update_data)


	def get_archive(self, database_client: DatabaseClient, project: str, run_identifier: str) -> dict:
		run = database_client.find_one(self.table, { "project": project, "identifier": run_identifier })
		if run is None:
			return None

		file_name = run_identifier + ".zip"
		now = time.gmtime()

		with io.BytesIO() as file_object:
			with zipfile.ZipFile(file_object, mode = "w", compression = zipfile.ZIP_DEFLATED) as archive:
				entry_info = zipfile.ZipInfo("run.json", now[0:6])
				entry_info.external_attr = 0o644 << 16
				archive.writestr(entry_info, json.dumps(run, indent = 4))
				for step in run.get("steps", []):
					log_path = self._get_step_log_path(database_client, project, run_identifier, step["index"])
					entry_info = zipfile.ZipInfo(os.path.basename(log_path), now[0:6])
					entry_info.external_attr = 0o644 << 16
					archive.writestr(entry_info, self.file_storage.load_or_default(log_path, ""))

			return { "file_name": file_name, "data": file_object.getvalue(), "type": "zip" }


	def convert_to_public(self, run: dict) -> dict: # pylint: disable = no-self-use
		keys_to_return = [
			"identifier", "project", "job", "worker", "parameters", "source", "status",
			"start_date", "completion_date", "should_cancel", "should_abort", "creation_date", "update_date",
		]

		return { key: value for key, value in run.items() if key in keys_to_return }

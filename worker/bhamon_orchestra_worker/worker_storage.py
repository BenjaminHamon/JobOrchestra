import logging
import os
import re
import shutil
from typing import Any, List, Optional

from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.serialization.serializer import Serializer


logger = logging.getLogger("WorkerStorage")


class WorkerStorage:


	def __init__(self, storage: FileDataStorage, serializer: Serializer) -> None:
		self._storage = storage
		self._serializer = serializer


	def list_runs(self) -> List[str]:
		request_file_regex = r"^runs/[a-zA-Z0-9_\-\.]+/request" + re.escape(self._serializer.get_file_extension()) + r"$"

		all_runs = []
		for key in self._storage.get_keys("runs/"):
			if re.search(request_file_regex, key) is not None:
				all_runs.append(key.split("/")[1])
		return all_runs


	def create_run(self, run_identifier: str) -> None:
		os.makedirs(self._storage.get_file_path("runs" + "/" + run_identifier))


	def delete_run(self, run_identifier: str) -> None:
		shutil.rmtree(self._storage.get_file_path("runs" + "/" + run_identifier))


	def run_exists(self, run_identifier: str) -> None:
		return os.path.isdir(self._storage.get_file_path("runs" + "/" + run_identifier))


	def load_request(self, run_identifier: str) -> dict:
		return self._load_data(run_identifier, "request")


	def save_request(self, run_identifier: str, request: dict) -> None:
		self._save_data(run_identifier, "request", request)


	def get_status_timestamp(self, run_identifier: str) -> Optional[float]:
		return self.get_timestamp(run_identifier, "status.json")


	def load_status(self, run_identifier: str) -> dict:
		return self._load_data(run_identifier, "status")


	def save_status(self, run_identifier: str, status: dict) -> None:
		self._save_data(run_identifier, "status", status)


	def get_results_timestamp(self, run_identifier: str) -> Optional[float]:
		return self.get_timestamp(run_identifier, "results.json")


	def load_results(self, run_identifier: str) -> dict:
		results = self._load_data(run_identifier, "results")
		return results if results is not None else {}


	def save_results(self, run_identifier: str, results: dict) -> None:
		self._save_data(run_identifier, "results", results)


	def get_log_path(self, run_identifier: str) -> str:
		return self._storage.get_file_path("runs" + "/" + run_identifier + "/" + "run.log")


	def get_timestamp(self, run_identifier: str, key: str) -> Optional[float]:
		key = "runs" + "/" + run_identifier + "/" + key
		file_path = self._storage.get_file_path(key)

		try:
			return os.path.getmtime(file_path)
		except FileNotFoundError:
			return None


	def _load_data(self, run_identifier: str, key: str) -> dict:
		key = "runs" + "/" + run_identifier + "/" + key + self._serializer.get_file_extension()
		with self._storage.lock(key):
			raw_data = self._storage.get(key)
		return self._serializer.deserialize_from_string(raw_data.decode("utf-8")) if raw_data is not None else None


	def _save_data(self, run_identifier: str, key: str, data: Any) -> None:
		key = "runs" + "/" + run_identifier + "/" + key + self._serializer.get_file_extension()
		serialized_data = self._serializer.serialize_to_string(data).encode("utf-8")
		with self._storage.lock(key):
			self._storage.set(key, serialized_data)

import logging

from typing import List, Optional, Tuple

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.run_provider import RunProvider


logger = logging.getLogger("WorkerProvider")


class WorkerProvider:


	def __init__(self, database_client: DatabaseClient, date_time_provider: DateTimeProvider) -> None:
		self.database_client = database_client
		self.date_time_provider = date_time_provider
		self.table = "worker"


	def count(self) -> int:
		return self.database_client.count(self.table, {})


	def get_list(self, skip: int = 0, limit: Optional[int] = None, order_by: Optional[Tuple[str,str]] = None) -> List[dict]:
		return self.database_client.find_many(self.table, {}, skip = skip, limit = limit, order_by = order_by)


	def get(self, worker_identifier: str) -> Optional[dict]:
		return self.database_client.find_one(self.table, { "identifier": worker_identifier })


	def create(self, worker_identifier: str, owner: str, version: str, display_name: str) -> dict:
		now = self.date_time_provider.now()

		worker = {
			"identifier": worker_identifier,
			"owner": owner,
			"version": version,
			"display_name": display_name,
			"properties": {},
			"is_enabled": True,
			"is_active": False,
			"creation_date": self.date_time_provider.serialize(now),
			"update_date": self.date_time_provider.serialize(now),
		}

		self.database_client.insert_one(self.table, worker)
		return worker


	def update_status(self, worker: dict, is_active: Optional[bool] = None, is_enabled: Optional[bool] = None, should_disconnect: Optional[bool] = None) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"is_active": is_active,
			"is_enabled": is_enabled,
			"should_disconnect": should_disconnect,
			"update_date": self.date_time_provider.serialize(now),
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		worker.update(update_data)
		self.database_client.update_one(self.table, { "identifier": worker["identifier"] }, update_data)


	def update_properties(self, worker: dict, version: str, display_name: str, properties: dict) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"version": version,
			"display_name": display_name,
			"properties": properties,
			"update_date": self.date_time_provider.serialize(now),
		}

		worker.update(update_data)
		self.database_client.update_one(self.table, { "identifier": worker["identifier"] }, update_data)


	def delete(self, worker_identifier: str, run_provider: RunProvider) -> None:
		worker_record = self.get(worker_identifier)
		if worker_record is None:
			raise ValueError("Worker '%s' does not exist" % worker_identifier)

		if worker_record["is_enabled"]:
			raise ValueError("Worker '%s' is enabled" % worker_identifier)
		if worker_record["is_active"]:
			raise ValueError("Worker '%s' is active" % worker_identifier)

		if run_provider.count(worker = worker_identifier, status = "pending") > 0:
			raise ValueError("Worker '%s' has pending runs" % worker_identifier)
		if run_provider.count(worker = worker_identifier, status = "running") > 0:
			raise ValueError("Worker '%s' has running runs" % worker_identifier)

		self.database_client.delete_one(self.table, { "identifier": worker_identifier })

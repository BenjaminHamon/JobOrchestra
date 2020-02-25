import logging
import uuid

from typing import List, Optional, Tuple

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.date_time_provider import DateTimeProvider


logger = logging.getLogger("TaskProvider")


class TaskProvider:


	def __init__(self, database_client: DatabaseClient, date_time_provider: DateTimeProvider) -> None:
		self.database_client = database_client
		self.date_time_provider = date_time_provider
		self.table = "task"


	def count(self, # pylint: disable = too-many-arguments
			type: Optional[str] = None, status: Optional[str] = None, # pylint: disable = redefined-builtin
			project: Optional[str] = None, run: Optional[str] = None, worker: Optional[str] = None) -> int:

		filter = { # pylint: disable = redefined-builtin
			"type": type,
			"status": status,
			"parameters.project_identifier": project,
			"parameters.run_identifier": run,
			"parameters.worker_identifier": worker,
		}

		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.table, filter)


	def get_list(self, # pylint: disable = too-many-arguments
			type: Optional[str] = None, status: Optional[str] = None, # pylint: disable = redefined-builtin
			project: Optional[str] = None, run: Optional[str] = None, worker: Optional[str] = None,
			skip: int = 0, limit: Optional[int] = None, order_by: Optional[Tuple[str,str]] = None) -> List[dict]:

		filter = { # pylint: disable = redefined-builtin
			"type": type,
			"status": status,
			"parameters.project_identifier": project,
			"parameters.run_identifier": run,
			"parameters.worker_identifier": worker,
		}

		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, task_identifier: str) -> Optional[dict]:
		return self.database_client.find_one(self.table, { "identifier": task_identifier })


	def create(self, type: str, parameters: dict) -> dict: # pylint: disable = redefined-builtin
		now = self.date_time_provider.now()

		task = {
			"identifier": str(uuid.uuid4()),
			"type": type,
			"parameters": parameters,
			"status": "pending",
			"should_cancel": False,
			"creation_date": self.date_time_provider.serialize(now),
			"update_date": self.date_time_provider.serialize(now),
		}

		self.database_client.insert_one(self.table, task)
		return task


	def update_status(self, task: dict, status: Optional[str] = None, should_cancel: Optional[bool] = None) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"status": status,
			"should_cancel": should_cancel,
			"update_date": self.date_time_provider.serialize(now),
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		task.update(update_data)
		self.database_client.update_one(self.table, { "identifier": task["identifier"] }, update_data)

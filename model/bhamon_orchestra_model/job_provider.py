import logging

from typing import List, Optional, Tuple

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.date_time_provider import DateTimeProvider


logger = logging.getLogger("JobProvider")


class JobProvider:


	def __init__(self, database_client: DatabaseClient, date_time_provider: DateTimeProvider) -> None:
		self.database_client = database_client
		self.date_time_provider = date_time_provider
		self.table = "job"


	def count(self, project: Optional[str] = None) -> int:
		filter = { "project": project } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.table, filter)


	def get_list(self, project: Optional[str] = None, skip: int = 0, limit: Optional[int] = None, order_by: Optional[Tuple[str,str]] = None) -> List[dict]:
		filter = { "project": project } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, job_identifier: str) -> Optional[dict]:
		return self.database_client.find_one(self.table, { "identifier": job_identifier })


	def create_or_update(self, # pylint: disable = too-many-arguments
			job_identifier: str, project: str, workspace: str, steps: list, parameters: list, properties: dict, description: str) -> dict:
		now = self.date_time_provider.now()
		job = self.get(job_identifier)

		if job is None:
			job = {
				"identifier": job_identifier,
				"project": project,
				"workspace": workspace,
				"steps": steps,
				"parameters": parameters,
				"properties": properties,
				"description": description,
				"is_enabled": True,
				"creation_date": self.date_time_provider.serialize(now),
				"update_date": self.date_time_provider.serialize(now),
			}

			self.database_client.insert_one(self.table, job)

		else:
			update_data = {
				"project": project,
				"workspace": workspace,
				"steps": steps,
				"parameters": parameters,
				"properties": properties,
				"description": description,
				"update_date": self.date_time_provider.serialize(now),
			}

			job.update(update_data)
			self.database_client.update_one(self.table, { "identifier": job_identifier }, update_data)

		return job


	def update_status(self, job: dict, is_enabled: Optional[bool] = None) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"is_enabled": is_enabled,
			"update_date": self.date_time_provider.serialize(now),
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		job.update(update_data)
		self.database_client.update_one(self.table, { "identifier": job["identifier"] }, update_data)


	def delete(self, job_identifier: str) -> None:
		self.database_client.delete_one(self.table, { "identifier": job_identifier })

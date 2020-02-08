import datetime
import logging


logger = logging.getLogger("ScheduleProvider")


class ScheduleProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "schedule"


	def count(self, project = None, job = None):
		filter = { "project": project, "job": job } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.table, filter)


	def get_list( # pylint: disable = too-many-arguments
			self, project = None, job = None, skip = 0, limit = None, order_by = None):
		filter = { "project": project, "job": job } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, schedule_identifier):
		return self.database_client.find_one(self.table, { "identifier": schedule_identifier })


	def create_or_update( # pylint: disable = too-many-arguments
			self, schedule_identifier, project_identifier, job_identifier, parameters, expression):
		schedule = self.get(schedule_identifier)

		if schedule is None:
			schedule = {
				"identifier": schedule_identifier,
				"project": project_identifier,
				"job": job_identifier,
				"parameters": parameters,
				"expression": expression,
				"is_enabled": False,
				"last_run": None,
				"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
				"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
			}

			self.database_client.insert_one(self.table, schedule)

		else:
			update_data = {
				"project": project_identifier,
				"job": job_identifier,
				"parameters": parameters,
				"expression": expression,
				"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
			}

			schedule.update(update_data)
			self.database_client.update_one(self.table, { "identifier": schedule_identifier }, update_data)

		return schedule


	def update_status(self, schedule, is_enabled = None, last_run = None):
		update_data = {}
		if is_enabled is not None:
			update_data["is_enabled"] = is_enabled
		if last_run is not None:
			update_data["last_run"] = last_run
		update_data["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"

		schedule.update(update_data)
		self.database_client.update_one(self.table, { "identifier": schedule["identifier"] }, schedule)


	def delete(self, schedule_identifier):
		self.database_client.delete_one(self.table, { "identifier": schedule_identifier })

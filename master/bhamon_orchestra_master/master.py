import asyncio
import logging

from typing import Callable

from bhamon_orchestra_master.job_scheduler import JobScheduler
from bhamon_orchestra_master.supervisor import Supervisor
from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider


logger = logging.getLogger("Master")


class Master:
	""" Main class for the master application """


	def __init__(self, # pylint: disable = too-many-arguments
			database_client_factory: Callable[[], DatabaseClient],
			project_provider: ProjectProvider, job_provider: JobProvider,
			schedule_provider: ScheduleProvider, worker_provider: WorkerProvider,
			job_scheduler: JobScheduler, supervisor: Supervisor) -> None:

		self._database_client_factory = database_client_factory
		self._project_provider = project_provider
		self._job_provider = job_provider
		self._schedule_provider = schedule_provider
		self._worker_provider = worker_provider
		self._job_scheduler = job_scheduler
		self._supervisor = supervisor


	async def run(self) -> None:
		""" Run the master """

		logger.info("Starting master")

		job_scheduler_future = asyncio.ensure_future(self._job_scheduler.run())
		supervisor_future = asyncio.ensure_future(self._supervisor.run_server())

		try:
			await asyncio.wait([ job_scheduler_future, supervisor_future ], return_when = asyncio.FIRST_COMPLETED)

		finally:
			job_scheduler_future.cancel()
			supervisor_future.cancel()

			try:
				await job_scheduler_future
			except asyncio.CancelledError:
				pass
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception from job scheduler", exc_info = True)

			try:
				await supervisor_future
			except asyncio.CancelledError:
				pass
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception from supervisor", exc_info = True)

			logger.info("Exiting master")


	def apply_configuration(self, configuration: dict) -> None:
		""" Save the provided configuration to the database """

		logger.info("Applying configuration")

		with self._database_client_factory() as database_client:
			for project in configuration["projects"]:
				logger.info("Adding/Updating project %s", project["identifier"])
				self._project_provider.create_or_update(database_client, project["identifier"], project["display_name"], project["services"])

				all_existing_jobs = self._job_provider.get_list(database_client, project = project["identifier"])
				for existing_job in all_existing_jobs:
					if existing_job["identifier"] not in [ job["identifier"] for job in project["jobs"] ]:
						logger.info("Removing project %s job %s", project["identifier"], existing_job["identifier"])
						self._job_provider.delete(database_client, project["identifier"], existing_job["identifier"])

				for job in project["jobs"]:
					logger.info("Adding/Updating project %s job %s", project["identifier"], job["identifier"])
					self._job_provider.create_or_update(database_client, job["identifier"], project["identifier"],
							**{ key: value for key, value in job.items() if key != "identifier" })

				all_existing_schedules = self._schedule_provider.get_list(database_client, project = project["identifier"])
				for existing_schedule in all_existing_schedules:
					if existing_schedule["identifier"] not in [ schedule["identifier"] for schedule in project["schedules"] ]:
						logger.info("Removing project %s schedule %s", project["identifier"], existing_schedule["identifier"])
						self._schedule_provider.delete(database_client, project["identifier"], existing_schedule["identifier"])

				for schedule in project["schedules"]:
					logger.info("Adding/Updating project %s schedule %s", project["identifier"], schedule["identifier"])
					self._schedule_provider.create_or_update(database_client, schedule["identifier"], project["identifier"],
							**{ key: value for key, value in schedule.items() if key != "identifier" })

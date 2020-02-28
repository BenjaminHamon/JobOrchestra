import asyncio
import logging
import platform
import signal


logger = logging.getLogger("Master")


class Master:


	def __init__(self, # pylint: disable = too-many-arguments
			project_provider, job_provider, schedule_provider, worker_provider, job_scheduler, supervisor):
		self._project_provider = project_provider
		self._job_provider = job_provider
		self._schedule_provider = schedule_provider
		self._worker_provider = worker_provider
		self._job_scheduler = job_scheduler
		self._supervisor = supervisor
		self._should_shutdown = False


	def run(self):
		logger.info("Starting master")

		if platform.system() == "Windows":
			signal.signal(signal.SIGBREAK, lambda signal_number, frame: self.shutdown()) # pylint: disable = no-member
		signal.signal(signal.SIGINT, lambda signal_number, frame: self.shutdown())
		signal.signal(signal.SIGTERM, lambda signal_number, frame: self.shutdown())

		asyncio_loop = asyncio.get_event_loop()
		asyncio_loop.run_until_complete(self.run_async())
		asyncio_loop.close()

		logger.info("Exiting master")


	async def run_async(self):
		shutdown_future = asyncio.ensure_future(self._watch_shutdown())
		job_scheduler_future = asyncio.ensure_future(self._job_scheduler.run())
		supervisor_future = asyncio.ensure_future(self._supervisor.run_server())

		try:
			await asyncio.wait([ shutdown_future, job_scheduler_future, supervisor_future ], return_when = asyncio.FIRST_COMPLETED)

		finally:
			shutdown_future.cancel()
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


	async def _watch_shutdown(self):
		while not self._should_shutdown:
			await asyncio.sleep(1)


	def apply_configuration(self, configuration):
		logger.info("Applying configuration")

		for project in configuration["projects"]:
			logger.info("Adding/Updating project %s", project["identifier"])
			self._project_provider.create_or_update(project["identifier"], project["display_name"], project["services"])

			all_existing_jobs = self._job_provider.get_list(project = project["identifier"])
			for existing_job in all_existing_jobs:
				if existing_job["identifier"] not in [ job["identifier"] for job in project["jobs"] ]:
					logger.info("Removing project %s job %s", project["identifier"], existing_job["identifier"])
					self._job_provider.delete(project["identifier"], existing_job["identifier"])

			for job in project["jobs"]:
				logger.info("Adding/Updating project %s job %s", project["identifier"], job["identifier"])
				self._job_provider.create_or_update(job["identifier"], project["identifier"], **{ key: value for key, value in job.items() if key != "identifier" })

			all_existing_schedules = self._schedule_provider.get_list(project = project["identifier"])
			for existing_schedule in all_existing_schedules:
				if existing_schedule["identifier"] not in [ schedule["identifier"] for schedule in project["schedules"] ]:
					logger.info("Removing project %s schedule %s", project["identifier"], existing_schedule["identifier"])
					self._schedule_provider.delete(project["identifier"], existing_schedule["identifier"])

			for schedule in project["schedules"]:
				logger.info("Adding/Updating project %s schedule %s", project["identifier"], schedule["identifier"])
				self._schedule_provider.create_or_update(schedule["identifier"], project["identifier"], **{ key: value for key, value in schedule.items() if key != "identifier" })


	def shutdown(self):
		self._should_shutdown = True

import asyncio
import logging
import platform
import signal


logger = logging.getLogger("Master")


class Master:


	def __init__( # pylint: disable = too-many-arguments
			self, job_scheduler, supervisor, task_processor, project_provider, job_provider, worker_provider, configuration_loader):
		self._job_scheduler = job_scheduler
		self._supervisor = supervisor
		self._task_processor = task_processor
		self._project_provider = project_provider
		self._job_provider = job_provider
		self._worker_provider = worker_provider
		self._configuration_loader = configuration_loader
		self._should_shutdown = False


	def run(self):
		logger.info("Starting master")

		if platform.system() == "Windows":
			signal.signal(signal.SIGBREAK, lambda signal_number, frame: self.shutdown()) # pylint: disable = no-member
		signal.signal(signal.SIGINT, lambda signal_number, frame: self.shutdown())
		signal.signal(signal.SIGTERM, lambda signal_number, frame: self.shutdown())

		self.reload_configuration()

		asyncio_loop = asyncio.get_event_loop()
		asyncio_loop.run_until_complete(self.run_async())
		asyncio_loop.close()

		logger.info("Exiting master")


	async def run_async(self):
		shutdown_future = asyncio.ensure_future(self._watch_shutdown())
		supervisor_future = asyncio.ensure_future(self._supervisor.run_server())
		task_processor_future = asyncio.ensure_future(self._task_processor.run())

		try:
			await asyncio.wait([ shutdown_future, supervisor_future, task_processor_future ], return_when = asyncio.FIRST_COMPLETED)

		finally:
			shutdown_future.cancel()
			supervisor_future.cancel()
			task_processor_future.cancel()

			try:
				await supervisor_future
			except asyncio.CancelledError:
				pass
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception from supervisor", exc_info = True)

			try:
				await task_processor_future
			except asyncio.CancelledError:
				pass
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception from task processor", exc_info = True)


	async def _watch_shutdown(self):
		while not self._should_shutdown:
			await asyncio.sleep(1)


	def register_default_tasks(self):
		self._task_processor.register_handler("reload_configuration", 20,
			lambda parameters: reload_configuration(self))
		self._task_processor.register_handler("stop_worker", 50,
			lambda parameters: stop_worker(self._supervisor, **parameters))
		self._task_processor.register_handler("abort_run", 80,
			lambda parameters: abort_run(self._job_scheduler, **parameters))
		self._task_processor.register_handler("cancel_run", 90,
			lambda parameters: cancel_run(self._job_scheduler, **parameters))


	def reload_configuration(self):
		logger.info("Reloading configuration")
		configuration = self._configuration_loader()

		for project in configuration["projects"]:
			logger.info("Adding/Updating project %s", project["identifier"])
			self._project_provider.create_or_update(project["identifier"], project["services"])

		all_existing_jobs = self._job_provider.get_list()
		for existing_job in all_existing_jobs:
			if existing_job["identifier"] not in [ job["identifier"] for job in configuration["jobs"] ]:
				logger.info("Removing job %s", existing_job["identifier"])
				self._job_provider.delete(existing_job["identifier"])

		for job in configuration["jobs"]:
			logger.info("Adding/Updating job %s", job["identifier"])
			self._job_provider.create_or_update(job["identifier"], job["project"], job["workspace"], job["steps"], job["parameters"], job["properties"], job["description"])


	def shutdown(self):
		self._should_shutdown = True


def reload_configuration(master):
	master.reload_configuration()
	return "succeeded"


def stop_worker(supervisor, worker_identifier):
	was_stopped = supervisor.stop_worker(worker_identifier)
	return "succeeded" if was_stopped else "failed"


def cancel_run(job_scheduler, run_identifier):
	was_cancelled = job_scheduler.cancel_run(run_identifier)
	return "succeeded" if was_cancelled else "failed"


def abort_run(job_scheduler, run_identifier):
	was_aborted = job_scheduler.abort_run(run_identifier)
	return "succeeded" if was_aborted else "failed"

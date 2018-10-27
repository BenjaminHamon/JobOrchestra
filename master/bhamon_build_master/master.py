import asyncio
import logging
import signal


logger = logging.getLogger("Master")


class Master:


	def __init__(self, supervisor, task_processor, job_provider, worker_provider, configuration_loader):
		self._supervisor = supervisor
		self._task_processor = task_processor
		self._job_provider = job_provider
		self._worker_provider = worker_provider
		self._configuration_loader = configuration_loader


	def run(self):
		logger.info("Starting build master")

		signal.signal(signal.SIGBREAK, lambda signal_number, frame: self.shutdown())
		signal.signal(signal.SIGINT, lambda signal_number, frame: self.shutdown())
		signal.signal(signal.SIGTERM, lambda signal_number, frame: self.shutdown())

		self.reload_configuration()

		main_future = asyncio.gather(self._supervisor.run_server(), self._task_processor.run())
		asyncio.get_event_loop().run_until_complete(main_future)

		logger.info("Exiting build master")


	def reload_configuration(self):
		logger.info("Reloading configuration")
		configuration = self._configuration_loader()

		all_existing_workers = self._worker_provider.get_all()
		for existing_worker_identifier in all_existing_workers.keys():
			if existing_worker_identifier not in [ worker["identifier"] for worker in configuration["workers"] ]:
				logger.info("Removing worker %s", existing_worker_identifier)
				self._worker_provider.delete(existing_worker_identifier)
				self._supervisor.stop_worker(existing_worker_identifier)
		all_existing_jobs = self._job_provider.get_all()
		for existing_job_identifier in all_existing_jobs.keys():
			if existing_job_identifier not in [ job["identifier"] for job in configuration["jobs"] ]:
				logger.info("Removing job %s", existing_job_identifier)
				self._job_provider.delete(existing_job_identifier)

		for worker in configuration["workers"]:
			logger.info("Adding/Updating worker %s", worker["identifier"])
			self._worker_provider.create_or_update(worker["identifier"], worker["properties"], worker["description"])
		for job in configuration["jobs"]:
			logger.info("Adding/Updating job %s", job["identifier"])
			self._job_provider.create_or_update(job["identifier"], job["workspace"], job["steps"], job["parameters"], job["properties"], job["description"])


	def shutdown(self):
		self._supervisor.shutdown()
		self._task_processor.shutdown()


def register_default_tasks(master):
	master._task_processor.register_handler("reload_configuration", 20,
		lambda parameters: reload_configuration(master))
	master._task_processor.register_handler("stop_worker", 50,
		lambda parameters: stop_worker(master._supervisor, **parameters))
	master._task_processor.register_handler("abort_build", 90,
		lambda parameters: abort_build(master._supervisor, **parameters))
	master._task_processor.register_handler("trigger_build", 100,
		lambda parameters: trigger_build(master._supervisor, **parameters),
		lambda parameters: cancel_build(master._supervisor, **parameters))


def reload_configuration(master):
	master.reload_configuration()
	return "succeeded"


def stop_worker(supervisor, worker_identifier):
	was_stopped = supervisor.stop_worker(worker_identifier)
	return "succeeded" if was_stopped else "failed"


def trigger_build(supervisor, build_identifier):
	was_triggered = supervisor.trigger_build(build_identifier)
	return "succeeded" if was_triggered else "pending"


def cancel_build(supervisor, build_identifier):
	was_cancelled = supervisor.cancel_build(build_identifier)
	return "succeeded" if was_cancelled else "failed"


def abort_build(supervisor, build_identifier):
	was_aborted = supervisor.abort_build(build_identifier)
	return "succeeded" if was_aborted else "failed"

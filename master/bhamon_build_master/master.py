import asyncio
import logging
import platform
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

		if platform.system() == "Windows":
			signal.signal(signal.SIGBREAK, lambda signal_number, frame: self.shutdown())
		signal.signal(signal.SIGINT, lambda signal_number, frame: self.shutdown())
		signal.signal(signal.SIGTERM, lambda signal_number, frame: self.shutdown())

		self.reload_configuration()

		main_future = asyncio.gather(self._supervisor.run_server(), self._task_processor.run())
		asyncio.get_event_loop().run_until_complete(main_future)

		logger.info("Exiting build master")


	def register_default_tasks(self):
		self._task_processor.register_handler("reload_configuration", 20,
			lambda parameters: reload_configuration(self))
		self._task_processor.register_handler("stop_worker", 50,
			lambda parameters: stop_worker(self._supervisor, **parameters))
		self._task_processor.register_handler("abort_build", 90,
			lambda parameters: abort_build(self._supervisor, **parameters))
		self._task_processor.register_handler("trigger_build", 100,
			lambda parameters: trigger_build(self._supervisor, **parameters),
			lambda parameters: cancel_build(self._supervisor, **parameters))


	def reload_configuration(self):
		logger.info("Reloading configuration")
		configuration = self._configuration_loader()

		all_existing_workers = self._worker_provider.get_list()
		for existing_worker in all_existing_workers:
			if existing_worker["identifier"] not in [ worker["identifier"] for worker in configuration["workers"] ]:
				logger.info("Removing worker %s", existing_worker["identifier"])
				self._worker_provider.delete(existing_worker["identifier"])
				self._supervisor.stop_worker(existing_worker["identifier"])
		all_existing_jobs = self._job_provider.get_list()
		for existing_job in all_existing_jobs:
			if existing_job["identifier"] not in [ job["identifier"] for job in configuration["jobs"] ]:
				logger.info("Removing job %s", existing_job["identifier"])
				self._job_provider.delete(existing_job["identifier"])

		for worker in configuration["workers"]:
			logger.info("Adding/Updating worker %s", worker["identifier"])
			self._worker_provider.create_or_update(worker["identifier"], worker["properties"], worker["description"])
		for job in configuration["jobs"]:
			logger.info("Adding/Updating job %s", job["identifier"])
			self._job_provider.create_or_update(job["identifier"], job["workspace"], job["steps"], job["parameters"], job["properties"], job["description"])


	def shutdown(self):
		self._supervisor.shutdown()
		self._task_processor.shutdown()


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

import asyncio
import logging


logger = logging.getLogger("Scheduler")

process_interval_seconds = 5


class Scheduler:


	def __init__(self, configuration, database, supervisor):
		self._configuration = configuration
		self._database = database
		self._supervisor = supervisor


	async def run(self):
		while True:
			self._process_pending_builds()
			await asyncio.sleep(process_interval_seconds)


	def _process_pending_builds(self):
		pending_builds = self._database.get_pending_builds()

		for build in pending_builds:
			try:
				self._start_build(build)
			except Exception:
				logger.warning("Failed to process pending build %s %s", build["job"], build["identifier"], exc_info = True)
				build["status"] = "exception"
			self._database.update_build(build)


	def _start_build(self, build):
		job = self._configuration.job_collection[build["job"]]
		job_workers = self._configuration.workers_by_job[build["job"]]
		avaiable_worker = self._supervisor.get_available_worker(job, job_workers)
		if avaiable_worker is None:
			return

		logger.info("Assigning build %s %s to worker %s", build["job"], build["identifier"], avaiable_worker.identifier)
		build["worker"] = avaiable_worker.identifier
		build["status"] = "running"
		avaiable_worker.assign_build(job, build)

import logging


logger = logging.getLogger("JobScheduler")


class JobScheduler:


	def __init__(self, supervisor, job_provider, build_provider, worker_selector):
		self._supervisor = supervisor
		self._job_provider = job_provider
		self._build_provider = build_provider
		self._worker_selector = worker_selector


	def trigger_build(self, build_identifier):
		build = self._build_provider.get(build_identifier)
		job = self._job_provider.get(build["job"])
		if not job["is_enabled"]:
			return False

		selected_worker = self._worker_selector(self._supervisor, job)
		if selected_worker is None:
			return False

		logger.info("Assigning build %s %s to worker %s", build["job"], build["identifier"], selected_worker)
		self._supervisor.get_worker(selected_worker).assign_build(job, build)
		return True


	def cancel_build(self, build_identifier):
		build = self._build_provider.get(build_identifier)
		if build["status"] != "pending":
			return False
		self._build_provider.update_status(build, status = "cancelled")
		return True


	def abort_build(self, build_identifier):
		build = self._build_provider.get(build_identifier)
		if build["status"] != "running":
			return False

		try:
			worker_instance = self._supervisor.get_worker(build["worker"])
		except KeyError:
			return False

		worker_instance.abort_build(build_identifier)
		return True

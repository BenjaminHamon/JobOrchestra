import asyncio
import logging

import pycron


logger = logging.getLogger("JobScheduler")


class JobScheduler:


	def __init__( # pylint: disable = too-many-arguments
			self, supervisor, date_time_provider, job_provider, run_provider, schedule_provider, worker_selector):
		self._supervisor = supervisor
		self._date_time_provider = date_time_provider
		self._job_provider = job_provider
		self._run_provider = run_provider
		self._schedule_provider = schedule_provider
		self._worker_selector = worker_selector
		self.update_interval_seconds = 10


	async def run(self):
		while True:
			try:
				await asyncio.gather(self.update(), asyncio.sleep(self.update_interval_seconds))
			except asyncio.CancelledError: # pylint: disable = try-except-raise
				raise
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception", exc_info = True)
				await asyncio.sleep(self.update_interval_seconds)


	async def update(self):
		now = self._date_time_provider.now().replace(second = 0)

		all_schedules = self._list_active_schedules()

		for schedule in all_schedules:
			if self._should_schedule_trigger(schedule, now):
				logger.info("Triggering run for schedule '%s'", schedule["identifier"])
				run = self._run_provider.create(schedule["project"], schedule["job"], schedule["parameters"])
				self._schedule_provider.update_status(schedule, last_run = run["identifier"])

		all_runs = self._list_pending_runs()

		for run in all_runs:
			try:
				self._trigger_run(run)
			except Exception: # pylint: disable = broad-except
				logger.error("Run trigger '%s' raised an exception", run["identifier"], exc_info = True)
				self._run_provider.update_status(run, status = "exception")


	def _list_active_schedules(self):
		all_schedules = self._schedule_provider.get_list()
		all_schedules = [ schedule for schedule in all_schedules if schedule["is_enabled"] ]
		return all_schedules


	def _list_pending_runs(self):
		all_runs = self._run_provider.get_list(status = "pending")
		all_runs = [ run for run in all_runs if run["worker"] is None ]
		return all_runs


	def _should_schedule_trigger(self, schedule, now):
		if not pycron.is_now(schedule["expression"], now):
			return False

		if schedule["last_run"] is None:
			return True

		last_run = self._run_provider.get(schedule["last_run"])
		if last_run is None:
			return True

		if last_run["status"] in [ "pending", "running" ]:
			return False

		last_trigger_date = self._date_time_provider.deserialize(last_run["creation_date"]).replace(second = 0)
		if last_trigger_date == now:
			return False

		return True


	def _trigger_run(self, run):
		job = self._job_provider.get(run["job"])
		if not job["is_enabled"]:
			return False

		selected_worker = self._worker_selector(self._supervisor, job)
		if selected_worker is None:
			return False

		logger.info("Assigning run '%s' '%s' to worker '%s'", run["job"], run["identifier"], selected_worker)
		self._supervisor.get_worker(selected_worker).assign_run(job, run)
		return True


	def cancel_run(self, run_identifier):
		run = self._run_provider.get(run_identifier)
		if run["status"] != "pending":
			return False
		self._run_provider.update_status(run, status = "cancelled")
		return True


	def abort_run(self, run_identifier):
		run = self._run_provider.get(run_identifier)
		if run["status"] != "running":
			return False

		try:
			worker_instance = self._supervisor.get_worker(run["worker"])
		except KeyError:
			return False

		worker_instance.abort_run(run_identifier)
		return True

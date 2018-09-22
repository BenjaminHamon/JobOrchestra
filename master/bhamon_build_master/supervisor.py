import asyncio
import functools
import logging

import websockets

import bhamon_build_master.worker as worker


logger = logging.getLogger("Supervisor")


class Supervisor:


	def __init__(self, host, port, worker_provider, job_provider, build_provider, worker_selector):
		self._active_workers = {}
		self._host = host
		self._port = port
		self._worker_provider = worker_provider
		self._job_provider = job_provider
		self._build_provider = build_provider
		self._worker_selector = worker_selector


	async def run_server(self):
		for worker_identifier in self._worker_provider.get_all().keys():
			self._worker_provider.update_status(worker_identifier, is_active = False)

		logger.info("Listening for workers on %s:%s", self._host, self._port)
		async with websockets.serve(self._process_connection, self._host, self._port):
			while True:
				await asyncio.sleep(1)


	def stop_worker(self, worker_identifier):
		if not worker_identifier in self._active_workers:
			return False
		logger.info("Requesting worker %s to shutdown", worker_identifier)
		self._active_workers[worker_identifier].shutdown()
		return True


	def trigger_build(self, build_identifier):
		build = self._build_provider.get(build_identifier)
		job = self._job_provider.get(build["job"])
		if not job["is_enabled"]:
			return False

		all_available_workers = []
		for worker_data in self._worker_provider.get_all().values():
			if worker_data["is_enabled"] and worker_data["is_active"]:
				all_available_workers.append((worker_data, self._active_workers[worker_data["identifier"]]))

		selected_worker = self._worker_selector(job, all_available_workers)
		if selected_worker is None:
			return False

		logger.info("Assigning build %s %s to worker %s", build["job"], build["identifier"], selected_worker.identifier)
		selected_worker.assign_build(job, build)
		return True


	def abort_build(self, build_identifier):
		for worker in self._active_workers.values():
			worker.abort_build(build_identifier)
		return True


	async def _process_connection(self, connection, path):
		worker_identifier = None

		try:
			logger.info("Processing connection: %s", connection)

			worker_authentication_response = await worker.Worker.authenticate(connection)
			worker_identifier = worker_authentication_response["identifier"]
			is_authenticated, reason = self._authenticate_worker(worker_identifier)
			if not is_authenticated:
				logger.warning("Refused connection from worker %s: %s", worker_identifier, reason)

			else:
				logger.info("Accepted connection from worker %s", worker_identifier)
				worker_instance = worker.Worker(worker_identifier, connection, self._build_provider)
				self._worker_provider.update_status(worker_identifier, is_active = True)
				self._active_workers[worker_identifier] = worker_instance

				try:
					await worker_instance.run()
				except websockets.exceptions.ConnectionClosed as exception:
					if exception.code not in [ 1000, 1001 ]:
						logger.error("Worker %s execution raised an exception", worker_identifier, exc_info = True)
				except:
					logger.error("Worker %s execution raised an exception", worker_identifier, exc_info = True)

				del self._active_workers[worker_identifier]
				if self._worker_provider.exists(worker_identifier):
					self._worker_provider.update_status(worker_identifier, is_active = False)
				logger.info("Closing connection with worker %s", worker_identifier)

		except:
			logger.error("Worker %s handler raised an exception", worker_identifier, exc_info = True)


	def _authenticate_worker(self, worker_identifier):
		if not self._worker_provider.exists(worker_identifier):
			return False, "Worker is unknown"
		if worker_identifier in self._active_workers:
			return False, "Worker is already connected"
		return True, ''

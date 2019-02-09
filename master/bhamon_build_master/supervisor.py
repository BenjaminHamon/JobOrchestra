import asyncio
import logging

import websockets

import bhamon_build_master.worker as worker


logger = logging.getLogger("Supervisor")


class Supervisor:


	def __init__(self, host, port, build_provider, job_provider, worker_provider, worker_selector):
		self._host = host
		self._port = port
		self._build_provider = build_provider
		self._job_provider = job_provider
		self._worker_provider = worker_provider
		self._worker_selector = worker_selector
		self._active_workers = {}
		self._should_shutdown = False
		self.update_interval_seconds = 10


	async def run_server(self):
		for worker_data in self._worker_provider.get_list():
			self._worker_provider.update_status(worker_data, is_active = False)

		logger.info("Listening for workers on %s:%s", self._host, self._port)
		async with websockets.serve(self._process_connection, self._host, self._port):
			while not self._should_shutdown or len(self._active_workers) > 0:
				await asyncio.sleep(1)


	def shutdown(self):
		for worker_instance in self._active_workers.values():
			worker_instance.should_disconnect = True
			worker_instance.wake_up()
		self._should_shutdown = True



	def stop_worker(self, worker_identifier):
		if not worker_identifier in self._active_workers:
			return False
		logger.info("Flagging worker %s for shutdown", worker_identifier)
		self._active_workers[worker_identifier].should_shutdown = True
		return True


	def trigger_build(self, build_identifier):
		build = self._build_provider.get(build_identifier)
		job = self._job_provider.get(build["job"])
		if not job["is_enabled"]:
			return False

		all_available_workers = []
		for worker_data in self._worker_provider.get_list():
			if worker_data["is_enabled"] and worker_data["is_active"]:
				all_available_workers.append((worker_data, self._active_workers[worker_data["identifier"]]))

		selected_worker = self._worker_selector(job, all_available_workers)
		if selected_worker is None:
			return False

		logger.info("Assigning build %s %s to worker %s", build["job"], build["identifier"], selected_worker.identifier)
		selected_worker.assign_build(job, build)
		return True


	def cancel_build(self, build_identifier):
		build = self._build_provider.get(build_identifier)
		if build["status"] != "pending":
			return False
		self._build_provider.update_status(build, status = "cancelled")
		return True


	def abort_build(self, build_identifier):
		for worker_instance in self._active_workers.values():
			worker_instance.abort_build(build_identifier)
		return True


	async def _process_connection(self, connection, path):
		worker_identifier = None
		if self._should_shutdown:
			return

		try:
			logger.info("Processing connection: %s", connection)

			worker_authentication_response = await worker.Worker.authenticate(connection)
			worker_identifier = worker_authentication_response["identifier"]
			worker_data = self._worker_provider.get(worker_identifier)
			is_authenticated, reason = self._authenticate_worker(worker_identifier, worker_data)
			if not is_authenticated:
				logger.warning("Refused connection from worker %s: %s", worker_identifier, reason)

			else:
				logger.info("Accepted connection from worker %s", worker_identifier)
				worker_instance = worker.Worker(worker_identifier, connection, self._build_provider)
				worker_instance.update_interval_seconds = self.update_interval_seconds
				self._worker_provider.update_status(worker_data, is_active = True)
				if worker_identifier in self._active_workers:
					raise KeyError("Worker %s is already in active workers" % worker_identifier)
				self._active_workers[worker_identifier] = worker_instance

				try:
					await worker_instance.run()
				except websockets.exceptions.ConnectionClosed as exception:
					if exception.code not in [ 1000, 1001 ]:
						logger.error("Worker %s execution raised an exception", worker_identifier, exc_info = True)
				except:
					logger.error("Worker %s execution raised an exception", worker_identifier, exc_info = True)

				del self._active_workers[worker_identifier]
				self._worker_provider.update_status(worker_data, is_active = False)
				logger.info("Closing connection with worker %s", worker_identifier)

		except:
			logger.error("Worker %s handler raised an exception", worker_identifier, exc_info = True)


	def _authenticate_worker(self, worker_identifier, worker_data):
		if worker_data is None:
			return False, "Worker is unknown"
		if worker_identifier in self._active_workers:
			return False, "Worker is already connected"
		return True, ''

import asyncio
import functools
import logging

import websockets

import bhamon_build_master.worker as worker


logger = logging.getLogger("Supervisor")


class Supervisor:


	def __init__(self, host, port, configuration, database, worker_provider):
		self._all_workers = {}
		self._host = host
		self._port = port
		self._configuration = configuration
		self._database = database
		self._worker_provider = worker_provider


	async def run_server(self):
		logger.info("Listening for workers on %s:%s", self._host, self._port)
		async with websockets.serve(self._process_connection, self._host, self._port):
			while True:
				await asyncio.sleep(1)


	def trigger_build(self, build_identifier):
		build = self._database.get_build(build_identifier)
		job = self._configuration.job_collection[build["job"]]
		job_workers = self._configuration.workers_by_job[build["job"]]

		all_available_workers = [ worker for worker in self._all_workers.values() if worker.is_idle() ]
		available_worker = next((worker for worker in all_available_workers if worker.identifier in job_workers), None)
		if available_worker is None:
			return False

		logger.info("Assigning build %s %s to worker %s", build["job"], build["identifier"], available_worker.identifier)
		available_worker.assign_build(job, build)
		return True


	def abort_build(self, build_identifier):
		worker_condition = lambda worker: worker.build is not None and worker.build["identifier"] == build_identifier
		build_worker = next((worker for worker in self._all_workers.values() if worker_condition(worker)), None)
		if build_worker is None:
			return False

		build_worker.abort_build()
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
				worker_instance = worker.Worker(worker_identifier, connection, self._database)
				self._worker_provider.update(worker_identifier, is_active = True)
				self._all_workers[worker_identifier] = worker_instance

				try:
					await worker_instance.run()
				except:
					logger.error("Worker %s execution raised an exception", worker_identifier, exc_info = True)

				del self._all_workers[worker_identifier]
				self._worker_provider.update(worker_identifier, is_active = False)
				logger.info("Closing connection with worker %s", worker_identifier)

		except:
			logger.error("Connection with worker %s raised an exception", worker_identifier, exc_info = True)


	def _authenticate_worker(self, worker_identifier):
		if not self._worker_provider.exists(worker_identifier):
			return False, "Worker is unknown"
		if worker_identifier in self._all_workers:
			return False, "Worker is already connected"
		return True, ''

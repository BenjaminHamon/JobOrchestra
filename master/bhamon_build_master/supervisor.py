import asyncio
import functools
import logging

import websockets

import bhamon_build_master.worker as worker


logger = logging.getLogger("Supervisor")


class Supervisor:


	def __init__(self, host, port, database):
		self._all_workers = []
		self._host = host
		self._port = port
		self._database = database


	async def run_server(self):
		logger.info("Listening for workers on %s:%s", self._host, self._port)
		async with websockets.serve(self._process_connection, self._host, self._port):
			while True:
				await asyncio.sleep(1)


	def get_available_worker(self, job, job_workers):
		all_available_workers = [ worker for worker in self._all_workers if worker.is_idle() ]
		return next((worker for worker in all_available_workers if worker.identifier in job_workers), None)


	async def _process_connection(self, connection, path):
		worker_identifier = None

		try:
			logger.info("Processing connection: %s", connection)

			worker_data = await worker.Worker.authenticate(connection)
			worker_identifier = worker_data["identifier"]
			is_authenticated, reason = self._authenticate_worker(worker_identifier)
			if not is_authenticated:
				logger.warning("Refused connection from worker %s: %s", worker_identifier, reason)

			else:
				logger.info("Accepted connection from worker %s", worker_identifier)
				worker_instance = worker.Worker(worker_identifier, connection, self._database)
				self._all_workers.append(worker_instance)

				try:
					await worker_instance.run()
				except:
					logger.error("Worker %s execution raised an exception", worker_identifier, exc_info = True)

				self._all_workers.remove(worker_instance)
				logger.info("Closing connection with worker %s", worker_identifier)

		except:
			logger.error("Connection with worker %s raised an exception", worker_identifier, exc_info = True)


	def _authenticate_worker(self, worker_identifier):
		known_workers = [ worker["identifier"] for worker in self._database.get_worker_collection() ]
		if worker_identifier not in known_workers:
			return False, "Worker is unknown"
		if any(worker.identifier == worker_identifier for worker in self._all_workers):
			return False, "Worker is already connected"
		return True, ''

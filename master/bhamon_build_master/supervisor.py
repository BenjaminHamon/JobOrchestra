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
		logger.info("Processing connection: %s", connection)
		authentication_result = await worker.Worker.authenticate(connection)
		worker_instance = worker.Worker(authentication_result["identifier"], connection, self._database)
		logger.info("Accepted connection from worker %s", worker_instance.identifier)
		self._all_workers.append(worker_instance)
		try:
			await worker_instance.run()
		except:
			logger.error("Worker %s raised an exception", worker_instance.identifier, exc_info = True)
		self._all_workers.remove(worker_instance)
		logger.info("Closing connection with worker %s", worker_instance.identifier)

import asyncio
import logging

import websockets

from bhamon_orchestra_model.network.websocket import WebSocketConnection
from bhamon_orchestra_master.worker import Worker, WorkerError
from bhamon_orchestra_master.worker_connection import WorkerConnection


logger = logging.getLogger("Supervisor")


class Supervisor:


	def __init__(self, host, port, run_provider, worker_provider, protocol_factory):
		self._host = host
		self._port = port
		self._run_provider = run_provider
		self._worker_provider = worker_provider
		self._protocol_factory = protocol_factory

		self._active_workers = {}
		self._should_shutdown = False
		self.update_interval_seconds = 10


	async def run_server(self):
		for worker_record in self._worker_provider.get_list():
			if worker_record["is_active"]:
				self._worker_provider.update_status(worker_record, is_active = False)

		logger.info("Listening for workers on '%s:%s'", self._host, self._port)
		async with websockets.serve(self._process_connection, self._host, self._port, create_protocol = self._protocol_factory, max_size = 2 ** 30):
			while not self._should_shutdown or len(self._active_workers) > 0:
				await asyncio.sleep(1)


	def shutdown(self):
		for worker_instance in self._active_workers.values():
			worker_instance.should_disconnect = True
			worker_instance.wake_up()
		self._should_shutdown = True


	def get_worker(self, worker_identifier):
		return self._active_workers[worker_identifier]


	def is_worker_available(self, worker_identifier):
		if worker_identifier not in self._active_workers:
			return False

		worker_record = self._worker_provider.get(worker_identifier)
		worker_instance = self._active_workers[worker_identifier]

		return worker_record["is_enabled"] and not worker_instance.should_shutdown


	def stop_worker(self, worker_identifier):
		if not worker_identifier in self._active_workers:
			return False
		logger.info("Flagging worker %s for shutdown", worker_identifier)
		self._active_workers[worker_identifier].should_shutdown = True
		return True


	async def _process_connection(self, connection, path): # pylint: disable = unused-argument
		if self._should_shutdown:
			return

		try:
			logger.info("Connection from worker '%s' (User: '%s', RemoteAddress: '%s')", connection.worker, connection.user, connection.remote_address[0])
			worker_connection = WorkerConnection(WebSocketConnection(connection))
			await self._process_connection_internal(connection.user, connection.worker, worker_connection)
		except WorkerError as exception:
			logger.error("Worker error: %s", exception)
		except Exception: # pylint: disable = broad-except
			logger.error("Unhandled exception in connection handler", exc_info = True)


	async def _process_connection_internal(self, user, worker_identifier, connection):
		logger.info("Registering worker '%s'", worker_identifier)
		properties = await connection.execute_command(None, "properties")
		worker_record = self._register_worker(worker_identifier, user, properties)
		worker_instance = self._instantiate_worker(worker_identifier, connection)

		self._worker_provider.update_status(worker_record, is_active = True)
		self._active_workers[worker_identifier] = worker_instance

		try:
			logger.info("Worker '%s' is now active", worker_identifier)
			await self._run_worker(worker_instance)

		finally:
			logger.info("Terminating connection with worker '%s'", worker_identifier)
			del self._active_workers[worker_identifier]
			self._worker_provider.update_status(worker_record, is_active = False)


	def _register_worker(self, worker_identifier, owner, properties):
		if worker_identifier in self._active_workers:
			raise WorkerError("Worker '%s' is already active" % worker_identifier)

		worker_record = self._worker_provider.get(worker_identifier)
		if worker_record is None:
			worker_record = self._worker_provider.create(worker_identifier, owner)
		if worker_record["owner"] != owner:
			raise WorkerError("Worker '%s' is owned by another user (Expected: '%s', Actual: '%s')" % (worker_identifier, worker_record["user"], owner))

		self._worker_provider.update_properties(worker_record, properties)

		return worker_record


	def _instantiate_worker(self, worker_identifier, connection):
		worker_instance = Worker(worker_identifier, connection, self._run_provider)
		worker_instance.update_interval_seconds = self.update_interval_seconds
		return worker_instance


	async def _run_worker(self, worker_instance):
		try:
			await worker_instance.run()
		except websockets.exceptions.ConnectionClosed as exception:
			if exception.code not in [ 1000, 1001 ]:
				logger.error("Lost connection with worker '%s'", worker_instance.identifier, exc_info = True)
		except Exception: # pylint: disable = broad-except
			logger.error("Unhandled exception from worker '%s'", worker_instance.identifier, exc_info = True)

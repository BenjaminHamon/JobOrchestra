import asyncio
import logging

import websockets

from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_model.network.websocket import WebSocketConnection
from bhamon_orchestra_master.worker import Worker, WorkerError


logger = logging.getLogger("Supervisor")


class Supervisor:


	def __init__( # pylint: disable = too-many-arguments
			self, host, port, run_provider, worker_provider, protocol_factory):
		self._host = host
		self._port = port
		self._run_provider = run_provider
		self._worker_provider = worker_provider
		self._protocol_factory = protocol_factory

		self._active_workers = {}


	async def run_server(self):
		for worker_record in self._worker_provider.get_list():
			if worker_record["is_active"]:
				self._worker_provider.update_status(worker_record, is_active = False)

		logger.info("Listening for workers on '%s:%s'", self._host, self._port)
		async with websockets.serve(self._process_connection, self._host, self._port, create_protocol = self._protocol_factory, max_size = 2 ** 30):
			while True:
				await asyncio.sleep(1)


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
		try:
			logger.info("Connection from worker '%s' (User: '%s', RemoteAddress: '%s')", connection.worker, connection.user, connection.remote_address[0])
			messenger_instance = Messenger(WebSocketConnection(connection))
			messenger_instance.identifier = connection.remote_address
			messenger_future = asyncio.ensure_future(messenger_instance.run())
			worker_future = asyncio.ensure_future(self._process_connection_internal(connection.user, connection.worker, messenger_instance))

			try:
				await asyncio.wait([ messenger_future, worker_future ], return_when = asyncio.FIRST_COMPLETED)

			finally:
				worker_future.cancel()
				messenger_future.cancel()
				messenger_instance.dispose()

				try:
					await worker_future
				except asyncio.CancelledError:
					pass
				except Exception: # pylint: disable = broad-except
					logger.error("Unhandled exception from worker '%s'", connection.worker, exc_info = True)

				try:
					await messenger_future
				except websockets.exceptions.ConnectionClosed as exception:
					if exception.code not in [ 1000, 1001 ] and not isinstance(exception.__cause__, asyncio.CancelledError):
						logger.error("Lost connection from worker '%s'", connection.worker, exc_info = True)
				except asyncio.CancelledError:
					pass
				except Exception as exception: # pylint: disable = broad-except
					logger.error("Unhandled exception from messenger", exc_info = True)

				logger.info("Terminating connection with worker '%s'", connection.worker)

		except WorkerError as exception:
			logger.error("Worker error: %s", exception)
		except Exception: # pylint: disable = broad-except
			logger.error("Unhandled exception in connection handler", exc_info = True)


	async def _process_connection_internal(self, user, worker_identifier, messenger_instance):
		logger.info("Registering worker '%s'", worker_identifier)
		properties = await messenger_instance.send_request({ "command": "properties" })
		worker_record = self._register_worker(worker_identifier, user, properties)
		worker_instance = self._instantiate_worker(worker_identifier, messenger_instance)

		self._worker_provider.update_status(worker_record, is_active = True)
		self._active_workers[worker_identifier] = worker_instance

		try:
			logger.info("Worker '%s' is now active", worker_identifier)
			await worker_instance.run()

		finally:
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


	def _instantiate_worker(self, worker_identifier, messenger_instance):
		worker_instance = Worker(worker_identifier, messenger_instance, self._run_provider)
		messenger_instance.update_handler = worker_instance.handle_update
		return worker_instance

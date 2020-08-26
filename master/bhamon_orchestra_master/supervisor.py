import asyncio
import logging

from typing import Callable, List, Type

import websockets

from bhamon_orchestra_master.protocol import WebSocketServerProtocol
from bhamon_orchestra_master.worker import Worker, WorkerError
from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_model.network.websocket import WebSocketConnection
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider


logger = logging.getLogger("Supervisor")


class Supervisor:


	def __init__(self, # pylint: disable = too-many-arguments
			host: str, port: str, protocol_factory: Type[WebSocketServerProtocol],
			database_client_factory: Callable[[], DatabaseClient], run_provider: RunProvider, worker_provider: WorkerProvider) -> None:

		self._host = host
		self._port = port
		self._protocol_factory = protocol_factory
		self._database_client_factory = database_client_factory
		self._run_provider = run_provider
		self._worker_provider = worker_provider

		self._active_workers = {}
		self.update_interval_seconds = 10


	async def run_server(self) -> None:
		""" Run the websocket server to handle worker connections """

		with self._database_client_factory() as database_client:
			for worker_record in self._worker_provider.get_list(database_client):
				if worker_record["is_active"]:
					self._worker_provider.update_status(database_client, worker_record, is_active = False, should_disconnect = False)

		logger.info("Listening for workers on '%s:%s'", self._host, self._port)
		async with websockets.serve(self._process_connection, self._host, self._port, create_protocol = self._protocol_factory):
			while True:
				try:
					with self._database_client_factory() as database_client:
						await asyncio.gather(self.update(database_client), asyncio.sleep(self.update_interval_seconds))
				except asyncio.CancelledError: # pylint: disable = try-except-raise
					raise
				except Exception: # pylint: disable = broad-except
					logger.error("Unhandled exception", exc_info = True)
					await asyncio.sleep(self.update_interval_seconds)


	def get_worker(self, worker_identifier: str) -> dict:
		""" Retrieve the instance for an active worker """
		return self._active_workers[worker_identifier]


	def is_worker_available(self, database_client: DatabaseClient, worker_identifier: str) -> bool:
		""" Check if a worker is available to execute runs """

		if worker_identifier not in self._active_workers:
			return False

		worker_record = self._worker_provider.get(database_client, worker_identifier)
		return worker_record["is_enabled"] and not worker_record["should_disconnect"]


	async def update(self, database_client: DatabaseClient) -> None:
		""" Perform a single update """

		all_worker_records = self._list_workers(database_client)

		for worker_record in all_worker_records:
			worker_instance = self._active_workers[worker_record["identifier"]]
			if worker_record["should_disconnect"]:
				worker_instance.should_disconnect = True


	def _list_workers(self, database_client: DatabaseClient) -> List[dict]:
		""" Retrieve all worker records from the database """
		all_workers = self._worker_provider.get_list(database_client)
		all_workers = [ worker for worker in all_workers if worker["identifier"] in self._active_workers ]
		return all_workers


	async def _process_connection(self, connection: WebSocketServerProtocol, path: str) -> None: # pylint: disable = unused-argument
		""" Wrapper around the connection processing to initialize objects and to handle cancellation and exceptions """

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
				except WorkerError as exception:
					logger.error("Worker error: %s", exception)
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

		except Exception: # pylint: disable = broad-except
			logger.error("Unhandled exception in connection handler", exc_info = True)


	async def _process_connection_internal(self, user: str, worker_identifier: str, messenger_instance: Messenger) -> None:
		""" Internal implementation for processing a worker connection """

		logger.info("Registering worker '%s'", worker_identifier)
		worker_properties = await messenger_instance.send_request({ "command": "describe" })

		with self._database_client_factory() as database_client:
			worker_record = self._register_worker(database_client, worker_identifier, user, **worker_properties)
			worker_instance = self._instantiate_worker(worker_identifier, messenger_instance)

			self._worker_provider.update_status(database_client, worker_record, is_active = True, should_disconnect = False)
			self._active_workers[worker_identifier] = worker_instance

		try:
			logger.info("Worker '%s' is now active", worker_identifier)
			await worker_instance.run()

		finally:
			del self._active_workers[worker_identifier]
			with self._database_client_factory() as database_client:
				self._worker_provider.update_status(database_client, worker_record, is_active = False, should_disconnect = False)


	def _register_worker(self, database_client: DatabaseClient, # pylint: disable = too-many-arguments
			worker_identifier: str, owner: str, version: str, display_name: str, properties: dict) -> dict:
		""" Register the worker by creating or updating its record in the database and checking it is valid """

		if worker_identifier in self._active_workers:
			raise WorkerError("Worker '%s' is already active" % worker_identifier)

		worker_record = self._worker_provider.get(database_client, worker_identifier)
		if worker_record is None:
			worker_record = self._worker_provider.create(database_client, worker_identifier, owner, version, display_name)
		if worker_record["owner"] != owner:
			raise WorkerError("Worker '%s' is owned by another user (Expected: '%s', Actual: '%s')" % (worker_identifier, worker_record["owner"], owner))

		self._worker_provider.update_properties(database_client, worker_record, version, display_name, properties)

		return worker_record


	def _instantiate_worker(self, worker_identifier: str, messenger_instance: Messenger) -> Worker:
		""" Instantiate a new worker object to watch the remote worker process """

		worker_instance = Worker(worker_identifier, messenger_instance, self._database_client_factory, self._run_provider)
		messenger_instance.update_handler = worker_instance.handle_update
		return worker_instance

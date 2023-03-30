import asyncio
import logging
from typing import Callable, List, Type

import websockets.server

from bhamon_orchestra_master.protocol import WebSocketServerProtocol
from bhamon_orchestra_master.worker import Worker
from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_model.network.websocket import WebSocketConnection
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer
from bhamon_orchestra_model.worker_provider import WorkerProvider


logger = logging.getLogger("Supervisor")


class RegistrationError(Exception):
	""" Exception class for worker registration errors """


class Supervisor:
	""" Supervisor managing worker connections to the master """


	def __init__(self, protocol_factory: Type[WebSocketServerProtocol],
			database_client_factory: Callable[[], DatabaseClient], run_provider: RunProvider, worker_provider: WorkerProvider) -> None:

		self._protocol_factory = protocol_factory
		self._database_client_factory = database_client_factory
		self._run_provider = run_provider
		self._worker_provider = worker_provider

		self._active_workers = {}
		self.update_interval_seconds = 10


	async def run_server(self, address: str, port: int) -> None:
		""" Run the websocket server to handle worker connections """

		with self._database_client_factory() as database_client:
			for worker_record in self._worker_provider.get_list(database_client):
				if worker_record["is_active"]:
					self._worker_provider.update_status(database_client, worker_record, is_active = False, should_disconnect = False)

		logger.info("Listening for workers on '%s:%s'", address, port)
		async with websockets.server.serve(self._try_process_connection, address, port, create_protocol = self._protocol_factory):
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


	async def _try_process_connection(self, connection: WebSocketServerProtocol, path: str) -> None: # pylint: disable = unused-argument
		""" Wrapper around the connection processing to handle exceptions """

		try:
			await self._process_connection(connection)
		except Exception: # pylint: disable = broad-except
			logger.error("Unhandled exception in connection handler for worker '%s'", connection.worker_identifier, exc_info = True)


	async def _process_connection(self, connection: WebSocketServerProtocol) -> None:
		""" Process the worker connection """

		logger.info("Worker '%s' connected (User: '%s', RemoteAddress: '%s')", connection.worker_identifier, connection.user_identifier, connection.remote_address[0])

		with self._database_client_factory() as database_client:
			try:
				worker_record = self._register_worker(database_client, connection.worker_identifier, connection.worker_version, connection.user_identifier)
			except RegistrationError:
				logger.error("Worker '%s' registration was refused", exc_info = True)
				return

		worker_instance = self._instantiate_worker(worker_record, connection)

		with self._database_client_factory() as database_client:
			self._worker_provider.update_status(database_client, worker_record, is_active = True, should_disconnect = False)
		self._active_workers[connection.worker_identifier] = worker_instance

		logger.info("Worker '%s' is now active", connection.worker_identifier)

		try:
			await worker_instance.run()

		finally:
			del self._active_workers[connection.worker_identifier]
			with self._database_client_factory() as database_client:
				self._worker_provider.update_status(database_client, worker_record, is_active = False, should_disconnect = False)

		logger.info("Worker '%s' disconnected", connection.worker_identifier)


	def _register_worker(self, database_client: DatabaseClient, worker_identifier: str, worker_version: str, user_identifier: str) -> dict:
		""" Register the worker by creating or updating its record in the database and checking it is valid """

		logger.info("Registering worker '%s'", worker_identifier)

		if worker_identifier in self._active_workers:
			raise RegistrationError("Worker '%s' is already active" % worker_identifier)

		worker_record = self._worker_provider.get(database_client, worker_identifier)
		if worker_record is None:
			worker_record = self._worker_provider.create(database_client, worker_identifier, user_identifier, worker_version, worker_identifier)

		if worker_record["owner"] != user_identifier:
			raise RegistrationError("Worker '%s' is owned by another user (Expected: '%s', Actual: '%s')" % (worker_identifier, worker_record["owner"], user_identifier))

		if worker_record["version"] != worker_version:
			self._worker_provider.update_properties(database_client, worker_record, version = worker_version)

		return worker_record


	def _instantiate_worker(self, worker_record: dict, connection: WebSocketServerProtocol) -> Worker:
		""" Instantiate a new worker object to watch the remote worker process """

		serializer_instance = JsonSerializer()
		messenger_instance = Messenger(serializer_instance, connection.remote_address[0], WebSocketConnection(connection))
		worker_instance = Worker(worker_record["identifier"], messenger_instance, self._database_client_factory, self._run_provider, self._worker_provider)
		messenger_instance.update_handler = worker_instance.receive_update

		return worker_instance

import asyncio
import logging

import websockets

from bhamon_build_master.worker import Worker, WorkerError
from bhamon_build_master.worker_connection import WorkerConnection


logger = logging.getLogger("Supervisor")


class Supervisor:


	def __init__(self, host, port, build_provider, worker_provider, user_provider, authentication_provider, authorization_provider):
		self._host = host
		self._port = port
		self._build_provider = build_provider
		self._worker_provider = worker_provider
		self._user_provider = user_provider
		self._authentication_provider = authentication_provider
		self._authorization_provider = authorization_provider
		self._active_workers = {}
		self._should_shutdown = False
		self.update_interval_seconds = 10


	async def run_server(self):
		for worker_data in self._worker_provider.get_list():
			self._worker_provider.update_status(worker_data, is_active = False)

		logger.info("Listening for workers on '%s:%s'", self._host, self._port)
		async with websockets.serve(self._process_connection, self._host, self._port, max_size = 2 ** 30):
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

		worker_data = self._worker_provider.get(worker_identifier)
		worker_instance = self._active_workers[worker_identifier]

		return worker_data["is_enabled"] and not worker_instance.should_shutdown


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
			worker_connection = WorkerConnection(connection)
			await self._process_connection_internal(worker_connection)
		except WorkerError as exception:
			logger.error("Worker error: %s", exception)
		except Exception: # pylint: disable = broad-except
			logger.error("Unhandled exception in connection handler", exc_info = True)


	async def _process_connection_internal(self, connection):
		logger.info("Receiving connection")
		authentication_data = await connection.execute_command(None, "authenticate")
		worker_identifier = authentication_data["worker"]

		logger.info("Checking authorization for worker '%s' (User: '%s')", worker_identifier, authentication_data.get("user", None))
		self._authorize_worker(worker_identifier, authentication_data.get("user", None), authentication_data.get("secret", None))

		logger.info("Registering worker '%s'", worker_identifier)
		worker_record = self._register_worker(worker_identifier)
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


	def _authorize_worker(self, worker, user, secret):
		if not self._authentication_provider.authenticate_with_token(user, secret):
			raise WorkerError("Authentication failed for worker '%s' (User: '%s')" % (worker, user))

		user_record = self._user_provider.get(user)
		if not self._authorization_provider.authorize_worker(user_record):
			raise WorkerError("Authorization failed for worker '%s' (User: '%s')" % (worker, user))


	def _register_worker(self, worker_identifier):
		if worker_identifier in self._active_workers:
			raise WorkerError("Worker '%s' is already active" % worker_identifier)

		worker_record = self._worker_provider.get(worker_identifier)
		if worker_record is None:
			raise WorkerError("Unknown worker '%s'" % worker_identifier)

		return worker_record


	def _instantiate_worker(self, worker_identifier, connection):
		worker_instance = Worker(worker_identifier, connection, self._build_provider)
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

import asyncio
import logging

import websockets

from bhamon_orchestra_model.network.exception import NetworkException


logger = logging.getLogger("WebSocket")


class WebSocketClient:


	def __init__(self, server_identifier, server_uri):
		self.server_identifier = server_identifier
		self.server_uri = server_uri


	async def run_once(self, connection_handler):
		logger.info("Connecting to %s on %s", self.server_identifier, self.server_uri)

		try:
			connection = await websockets.connect(self.server_uri)
		except OSError as exception:
			raise NetworkException from exception

		try:
			logger.info("Connected to %s", self.server_identifier)
			await connection_handler(WebSocketConnection(connection))
		except websockets.exceptions.ConnectionClosed as exception:
			if exception.code not in [ 1000, 1001 ]:
				raise
			await connection.close() # If the connection was closed by the server, it is not marked as closed on the client
			logger.info("Closed connection to %s", self.server_identifier)
		finally:
			if not connection.closed:
				await connection.close()
				logger.info("Closed connection to %s", self.server_identifier)


	async def run_forever(self, connection_handler, connection_attempt_delay_collection = None):
		if connection_attempt_delay_collection is None:
			connection_attempt_delay_collection = [ 10, 10, 10, 10, 10, 60, 60, 60, 300, 3600 ]

		connection_attempt_counter = 0

		while True:
			try:
				connection_attempt_counter += 1
				logger.info("Connecting to %s on %s (Attempt: %s)", self.server_identifier, self.server_uri, connection_attempt_counter)

				try:
					connection = await websockets.connect(self.server_uri)
				except OSError as exception:
					raise NetworkException from exception

				try:
					connection_attempt_counter = 0
					logger.info("Connected to %s", self.server_identifier)
					await connection_handler(WebSocketConnection(connection))
				except websockets.exceptions.ConnectionClosed as exception:
					if exception.code not in [ 1000, 1001 ]:
						raise
					await connection.close() # If the connection was closed by the server, it is not marked as closed on the client
					logger.info("Closed connection to %s", self.server_identifier)
				finally:
					if not connection.closed:
						await connection.close()
						logger.info("Closed connection to %s", self.server_identifier)

			except NetworkException:
				logger.error("Failed to connect to %s", self.server_identifier, exc_info = True)
			except websockets.exceptions.InvalidStatusCode:
				logger.error("Failed to connect to %s", self.server_identifier, exc_info = True)
			except websockets.exceptions.ConnectionClosed:
				logger.error("Lost connection to %s", self.server_identifier, exc_info = True)

			try:
				connection_attempt_delay = connection_attempt_delay_collection[connection_attempt_counter]
			except IndexError:
				connection_attempt_delay = connection_attempt_delay_collection[-1]
			logger.info("Retrying connection in %s seconds", connection_attempt_delay)
			await asyncio.sleep(connection_attempt_delay)



class WebSocketConnection:


	def __init__(self, connection):
		self.connection = connection


	async def ping(self):
		return await self.connection.ping()


	async def send(self, data):
		await self.connection.send(data)


	async def receive(self):
		return await self.connection.recv()

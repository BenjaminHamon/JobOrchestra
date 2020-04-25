import asyncio
import logging

from typing import Callable

import websockets

from bhamon_orchestra_model.network.connection import NetworkConnection


logger = logging.getLogger("WebSocket")



class WebSocketConnection(NetworkConnection):
	""" Network connection implementation for WebSocket """


	def __init__(self, connection: websockets.WebSocketClientProtocol) -> None:
		self.connection = connection


	async def ping(self) -> None:
		""" Send a ping """
		return await self.connection.ping()


	async def send(self, data: str) -> None:
		""" Send a message """
		await self.connection.send(data)


	async def receive(self) -> str:
		""" Receive the next message """
		return await self.connection.recv()



class WebSocketClient:


	def __init__(self, server_identifier: str, server_uri: str) -> None:
		self.server_identifier = server_identifier
		self.server_uri = server_uri

		self.connection_attempt_delay_collection = [ 10, 10, 10, 10, 10, 60, 60, 60, 300, 3600 ]


	async def run_once(self, connection_handler: Callable[[WebSocketConnection],None], **kwargs) -> None:
		logger.info("Connecting to %s (Uri: '%s')", self.server_identifier, self.server_uri)
		connection = await websockets.connect(self.server_uri, **kwargs)

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


	async def run_forever(self, connection_handler: Callable[[WebSocketConnection],None], **kwargs) -> None:
		connection_attempt_counter = 0

		while True:
			try:
				connection_attempt_counter += 1
				logger.info("Connecting to %s on %s (Attempt: %s)", self.server_identifier, self.server_uri, connection_attempt_counter)
				connection = await websockets.connect(self.server_uri, **kwargs)

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

			except ConnectionError:
				logger.error("Failed to connect to %s", self.server_identifier, exc_info = True)
			except websockets.exceptions.InvalidStatusCode:
				logger.error("Failed to connect to %s", self.server_identifier, exc_info = True)
			except websockets.exceptions.ConnectionClosed:
				logger.error("Lost connection to %s", self.server_identifier, exc_info = True)

			try:
				connection_attempt_delay = self.connection_attempt_delay_collection[connection_attempt_counter]
			except IndexError:
				connection_attempt_delay = self.connection_attempt_delay_collection[-1]
			logger.info("Retrying connection in %s seconds", connection_attempt_delay)
			await asyncio.sleep(connection_attempt_delay)

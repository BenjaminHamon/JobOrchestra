import base64
import logging
import http

from typing import Any, Awaitable, Callable

import websockets
import websockets.http

from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.user_provider import UserProvider


logger = logging.getLogger("WebSocket")


class WebSocketServerProtocol(websockets.WebSocketServerProtocol):
	""" WebSocket server protocol implementation, extended to process connections from workers """


	def __init__(self, # pylint: disable = too-many-arguments
			ws_handler: Callable[["WebSocketServerProtocol", str], Awaitable[Any]], ws_server: "WebSocketServer",
			database_client_factory: Callable[[], DatabaseClient], user_provider: UserProvider,
			authentication_provider: AuthenticationProvider, authorization_provider: AuthorizationProvider, **kwargs) -> None:

		super().__init__(ws_handler, ws_server, **kwargs)

		self._database_client_factory = database_client_factory
		self._user_provider = user_provider
		self._authentication_provider = authentication_provider
		self._authorization_provider = authorization_provider

		self.user = None
		self.worker = None


	async def process_request(self, path: str, request_headers: websockets.http.Headers) -> tuple: # pylint: disable = invalid-overridden-method
		""" Process the incoming HTTP request """

		try:
			try:
				with self._database_client_factory() as database_client:
					self._authorize_request(database_client, request_headers)
			except ValueError as exception:
				raise HttpError(http.HTTPStatus.UNAUTHORIZED) from exception
		except HttpError as exception:
			logger.error("Request error: %s (%s)", exception.status.phrase, exception.status.value, exc_info = True)
			return (exception.status, [], (exception.status.phrase + "\n").encode())

		return await super().process_request(path, request_headers)


	def _authorize_request(self, database_client: DatabaseClient, request_headers: websockets.http.Headers) -> None:
		""" Check if the websocket connection is authorized and can proceed, otherwise raise an HTTP error """

		if "Authorization" not in request_headers or "X-Orchestra-Worker" not in request_headers:
			raise HttpError(http.HTTPStatus.FORBIDDEN)

		self.worker = request_headers["X-Orchestra-Worker"]
		if not self.worker:
			raise HttpError(http.HTTPStatus.FORBIDDEN)

		self.user = self._authorize_worker(database_client, request_headers["Authorization"])


	def _authorize_worker(self, database_client: DatabaseClient, authorization: str) -> str:
		""" Check if the worker is authorized to connect to the master, otherwise raise an HTTP error """

		authentication_type, authentication_data = authorization.split(" ", 1)
		if authentication_type != "Basic":
			raise HttpError(http.HTTPStatus.FORBIDDEN)

		user, secret = base64.b64decode(authentication_data.encode()).decode().split(":", 1)
		if not self._authentication_provider.authenticate_with_token(database_client, user, secret):
			raise HttpError(http.HTTPStatus.UNAUTHORIZED)

		user_record = self._user_provider.get(database_client, user)
		if not self._authorization_provider.authorize_worker(user_record):
			raise HttpError(http.HTTPStatus.FORBIDDEN)

		return user



class HttpError(Exception):
	""" Exception class for HTTP errors """

	def __init__(self, status: http.HTTPStatus):
		super().__init__()
		self.status = status

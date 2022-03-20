import base64
import logging

from http import HTTPStatus as HttpStatus
from typing import Any, Awaitable, Callable, Optional

from websockets.datastructures import Headers
from websockets.legacy.server import HTTPResponse as HttpResponse
from websockets.legacy.server import WebSocketServerProtocol as BaseWebSocketServerProtocol

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.users.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.users.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.users.user_provider import UserProvider


logger = logging.getLogger("WebSocket")


class WebSocketServerProtocol(BaseWebSocketServerProtocol):
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

		self.user_identifier = None
		self.worker_identifier = None
		self.worker_version = None


	async def process_request(self, path: str, request_headers: Headers) -> Optional[HttpResponse]:
		""" Process the incoming HTTP request """

		try:
			try:
				with self._database_client_factory() as database_client:
					self._authorize_request(database_client, request_headers)
			except ValueError as exception:
				raise HttpError(HttpStatus.UNAUTHORIZED) from exception
		except HttpError as exception:
			logger.error("Request error: %s (%s)", exception.status.phrase, exception.status.value, exc_info = True)
			return (exception.status, [], (exception.status.phrase + "\n").encode())

		return await super().process_request(path, request_headers)


	def _authorize_request(self, database_client: DatabaseClient, request_headers: Headers) -> None:
		""" Check if the websocket connection is authorized and can proceed, otherwise raise an HTTP error """

		if "Authorization" not in request_headers:
			raise HttpError(HttpStatus.FORBIDDEN)

		self.worker_identifier = request_headers.get("X-Orchestra-WorkerIdentifier", None)
		if self.worker_identifier is None or self.worker_identifier == "":
			raise HttpError(HttpStatus.BAD_REQUEST)

		self.worker_version = request_headers.get("X-Orchestra-WorkerVersion", None)
		if self.worker_version is None or self.worker_version == "":
			raise HttpError(HttpStatus.BAD_REQUEST)

		self.user_identifier = self._authorize_worker(database_client, request_headers["Authorization"])


	def _authorize_worker(self, database_client: DatabaseClient, authorization: str) -> str:
		""" Check if the worker is authorized to connect to the master, otherwise raise an HTTP error """

		authentication_type, authentication_data = authorization.split(" ", 1)
		if authentication_type != "Basic":
			raise HttpError(HttpStatus.FORBIDDEN)

		user, secret = base64.b64decode(authentication_data.encode()).decode().split(":", 1)
		if not self._authentication_provider.authenticate_with_token(database_client, user, secret):
			raise HttpError(HttpStatus.UNAUTHORIZED)

		user_record = self._user_provider.get(database_client, user)
		if not self._authorization_provider.authorize_worker(user_record):
			raise HttpError(HttpStatus.FORBIDDEN)

		return user



class HttpError(Exception):
	""" Exception class for HTTP errors """

	def __init__(self, status: HttpStatus):
		super().__init__()
		self.status = status

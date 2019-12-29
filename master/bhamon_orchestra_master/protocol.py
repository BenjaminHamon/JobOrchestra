import base64
import logging
import http

import websockets


logger = logging.getLogger("WebSocket")


class WebSocketServerProtocol(websockets.WebSocketServerProtocol):


	def __init__(self, ws_handler, ws_server, user_provider, authentication_provider, authorization_provider, **kwargs):
		self._user_provider = user_provider
		self._authentication_provider = authentication_provider
		self._authorization_provider = authorization_provider

		self.user = None
		self.worker = None

		super().__init__(ws_handler, ws_server, **kwargs)


	async def process_request(self, path, request_headers): # pylint: disable = method-hidden
		try:
			try:
				self._authorize_request(request_headers)
			except ValueError as exception:
				raise HttpError(http.HTTPStatus.UNAUTHORIZED) from exception
		except HttpError as exception:
			logger.error("Request error: %s (%s)", exception.status.phrase, exception.status.value, exc_info = True)
			return (exception.status, [], (exception.status.phrase + "\n").encode())

		return await super().process_request(path, request_headers)


	def _authorize_request(self, request_headers):
		if "Authorization" not in request_headers or "X-Orchestra-Worker" not in request_headers:
			raise HttpError(http.HTTPStatus.FORBIDDEN)

		self.worker = request_headers["X-Orchestra-Worker"]
		if not self.worker:
			raise HttpError(http.HTTPStatus.FORBIDDEN)

		self.user = self._authorize_worker(request_headers["Authorization"])


	def _authorize_worker(self, authorization):
		authentication_type, authentication_data = authorization.split(" ", 1)
		if authentication_type != "Basic":
			raise HttpError(http.HTTPStatus.FORBIDDEN)

		user, secret = base64.b64decode(authentication_data.encode()).decode().split(":", 1)
		if not self._authentication_provider.authenticate_with_token(user, secret):
			raise HttpError(http.HTTPStatus.UNAUTHORIZED)

		user_record = self._user_provider.get(user)
		if not self._authorization_provider.authorize_worker(user_record):
			raise HttpError(http.HTTPStatus.FORBIDDEN)

		return user



class HttpError(Exception):

	def __init__(self, status):
		self.status = status
		super().__init__()

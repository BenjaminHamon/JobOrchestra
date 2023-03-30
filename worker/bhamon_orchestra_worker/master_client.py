import base64
import logging
from typing import Awaitable, Callable

from bhamon_orchestra_model.network.websocket import WebSocketClient
from bhamon_orchestra_model.network.websocket import WebSocketConnection


logger = logging.getLogger("MasterClient")


class MasterClient: # pylint: disable = too-few-public-methods


	def __init__(self, # pylint: disable = too-many-arguments
			master_uri: str, worker_identifier: str, worker_version: str, user: str, secret: str) -> None:

		self.master_uri = master_uri
		self.worker_identifier = worker_identifier
		self.worker_version = worker_version

		self._user = user
		self._secret = secret


	async def run(self, connection_handler: Callable[[WebSocketConnection],Awaitable[None]]) -> None:
		websocket_client_instance = WebSocketClient("master", self.master_uri)
		authentication_data = base64.b64encode(b"%s:%s" % (self._user.encode(), self._secret.encode())).decode()

		headers = {
			"Authorization": "Basic" + " " + authentication_data,
		 	"X-Orchestra-WorkerIdentifier": self.worker_identifier,
			"X-Orchestra-WorkerVersion": self.worker_version,
		}

		await websocket_client_instance.run_forever(connection_handler, extra_headers = headers)

import asyncio
import json
import logging
import traceback
import uuid

from typing import Callable, Dict, List, Optional

from bhamon_orchestra_model.network.connection import NetworkConnection


logger = logging.getLogger("Messenger")


class Messenger:


	def __init__(self, connection: NetworkConnection) -> None:
		self.connection = connection

		self.identifier: str = None
		self.request_handler: Optional[Callable[[dict],dict]] = None
		self.update_handler: Optional[Callable[[dict],dict]] = None
		self.messages_to_send: List[dict] = []
		self.messages_to_wait: List[dict] = []
		self.messages_to_handle: List[dict] = []
		self._messages_events: Dict[str,asyncio.Event] = {}
		self.is_disposed = False


	async def run(self) -> None:
		if self.is_disposed:
			raise RuntimeError("Messenger is disposed")

		incoming_future = asyncio.ensure_future(self._pull())
		incoming_process_future = asyncio.ensure_future(self._handle_incoming())
		outgoing_future = asyncio.ensure_future(self._push())

		try:
			await asyncio.gather(incoming_future, incoming_process_future, outgoing_future)

		finally:
			incoming_future.cancel()
			incoming_process_future.cancel()
			outgoing_future.cancel()


	def dispose(self) -> None:
		for message in self.messages_to_send:
			logger.warning("Cancelling outgoing %s %s", message["type"], message["identifier"])

		for message in self.messages_to_wait:
			logger.warning("Cancelling expected response %s", message["identifier"])
			self._handle_response({ "identifier": message["identifier"], "error": "Cancelled" })

		for message in self.messages_to_handle:
			logger.warning("Cancelling handling %s %s", message["type"], message["identifier"])

		self.messages_to_send = []
		self.messages_to_wait = []
		self.messages_to_handle = []
		self._messages_events = {}

		self.is_disposed = True


	async def send_request(self, data: dict) -> None:
		if self.is_disposed:
			raise RuntimeError("Messenger is disposed")

		identifier = str(uuid.uuid4())
		message_event = asyncio.Event()
		message = { "type": "request", "identifier": identifier, "data": data }

		self._messages_events[identifier] = message_event
		self.messages_to_send.append(message)

		await message_event.wait()

		if message["response"].get("error", None) is not None:
			raise RuntimeError(message["response"]["error"])
		return message["response"].get("data", None)


	def _send_response(self, identifier: str, data: dict) -> None:
		message = { "type": "response", "identifier": identifier, "data": data }
		self.messages_to_send.append(message)


	def _send_response_error(self, identifier: str, error: dict) -> None:
		message = { "type": "response", "identifier": identifier, "error": error }
		self.messages_to_send.append(message)


	def send_update(self, data: dict) -> None:
		if self.is_disposed:
			raise RuntimeError("Messenger is disposed")

		identifier = str(uuid.uuid4())
		message = { "type": "update", "identifier": identifier, "data": data }
		self.messages_to_send.append(message)


	async def _push(self) -> None:
		while True:
			while len(self.messages_to_send) > 0:
				await self._send_next()
			await asyncio.sleep(0.1)


	async def _send_next(self) -> None:
		if len(self.messages_to_send) == 0:
			return

		message = self.messages_to_send[0]
		logger.debug("(%s) > %s %s", self.identifier, message["type"], message["identifier"])
		await self.connection.send(json.dumps(message))
		self.messages_to_send.remove(message)

		if message["type"] == "request":
			self.messages_to_wait.append(message)


	async def _pull(self) -> None:
		while True:
			try:
				await self._receive_next()
			except asyncio.TimeoutError:
				pass


	async def _receive_next(self) -> None:
		message = json.loads(await asyncio.wait_for(self.connection.receive(), 1))
		logger.debug("(%s) < %s %s", self.identifier, message["type"], message["identifier"])
		self.messages_to_handle.append(message)


	async def _handle_incoming(self) -> None:
		while True:
			while len(self.messages_to_handle) > 0:
				await self._handle_next()
			await asyncio.sleep(0.1)


	async def _handle_next(self) -> None:
		if len(self.messages_to_handle) == 0:
			return

		message = self.messages_to_handle[0]

		try:
			message_was_handled = await self._handle_message(message)
			if message_was_handled:
				self.messages_to_handle.remove(message)
		except Exception: # pylint: disable = broad-except
			logger.error("Unhandled exception in message handler", exc_info = True)


	async def _handle_message(self, message: dict) -> bool:
		if message["type"] == "request":
			return await self._handle_request(message)
		if message["type"] == "response":
			return await self._handle_response(message)
		if message["type"] == "update":
			return await self._handle_update(message)
		raise ValueError("Unsupported message type: '%s'" % message["type"])


	async def _handle_request(self, request: dict) -> bool:
		if self.request_handler is None:
			return False

		logger.debug("Handling request '%s'", request["identifier"])

		try:
			result = await self.request_handler(request["data"]) # pylint: disable = not-callable
			self._send_response(request["identifier"], result)
		except Exception as exception: # pylint: disable = broad-except
			logger.error("Handler for request '%s' raised an exception", request["identifier"], exc_info = True)
			error_result = "".join(traceback.format_exception_only(exception.__class__, exception)).strip()
			self._send_response_error(request["identifier"], error_result)

		return True


	async def _handle_response(self, response: dict) -> bool:
		logger.debug("Handling response '%s'", response["identifier"])

		request = next(r for r in self.messages_to_wait if r["type"] == "request" and r["identifier"] == response["identifier"])
		request["response"] = response
		self._messages_events[request["identifier"]].set()
		self.messages_to_wait.remove(request)
		return True


	async def _handle_update(self, update: dict) -> bool:
		if self.update_handler is None:
			return False

		logger.debug("Handling update '%s'", update["identifier"])

		try:
			await self.update_handler(update["data"]) # pylint: disable = not-callable
		except Exception: # pylint: disable = broad-except
			logger.error("Handler for update '%s' raised an exception", update["identifier"], exc_info = True)
		return True

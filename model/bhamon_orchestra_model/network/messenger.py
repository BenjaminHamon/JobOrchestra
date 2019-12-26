import asyncio
import json
import logging
import traceback
import uuid


logger = logging.getLogger("Messenger")


class Messenger:


	def __init__(self, connection):
		self.connection = connection

		self.identifier = None
		self.request_handler = None
		self.messages_to_send = []
		self.messages_to_wait = []
		self.messages_to_handle = []
		self._messages_events = {}
		self.is_disposed = False


	async def run(self):
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


	def dispose(self):
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


	async def send_request(self, data):
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


	def _send_response(self, identifier, data):
		message = { "type": "response", "identifier": identifier, "data": data }
		self.messages_to_send.append(message)


	def _send_response_error(self, identifier, error):
		message = { "type": "response", "identifier": identifier, "error": error }
		self.messages_to_send.append(message)


	async def _push(self):
		while True:
			while len(self.messages_to_send) > 0:
				await self._send_next()
			await asyncio.sleep(0.1)


	async def _send_next(self):
		if len(self.messages_to_send) == 0:
			return

		message = self.messages_to_send[0]
		logger.debug("(%s) > %s %s", self.identifier, message["type"], message["identifier"])
		await self.connection.send(json.dumps(message))
		self.messages_to_send.remove(message)

		if message["type"] == "request":
			self.messages_to_wait.append(message)


	async def _pull(self):
		while True:
			try:
				await self._receive_next()
			except asyncio.TimeoutError:
				pass


	async def _receive_next(self):
		message = json.loads(await asyncio.wait_for(self.connection.receive(), 1))
		logger.debug("(%s) < %s %s", self.identifier, message["type"], message["identifier"])
		self.messages_to_handle.append(message)


	async def _handle_incoming(self):
		while True:
			while len(self.messages_to_handle) > 0:
				await self._handle_next()
			await asyncio.sleep(0.1)


	async def _handle_next(self):
		if len(self.messages_to_handle) == 0:
			return

		message = self.messages_to_handle[0]
		if message["type"] == "request":
			await self._handle_request(message)
		elif message["type"] == "response":
			self._handle_response(message)
		self.messages_to_handle.remove(message)


	async def _handle_request(self, request):
		try:
			result = await self.request_handler(request["data"]) # pylint: disable = not-callable
			self._send_response(request["identifier"], result)
		except Exception as exception: # pylint: disable = broad-except
			logger.error("Request %s exception", request["identifier"], exc_info = True)
			error_result = "".join(traceback.format_exception_only(exception.__class__, exception)).strip()
			self._send_response_error(request["identifier"], error_result)


	def _handle_response(self, response):
		request = next(r for r in self.messages_to_wait if r["type"] == "request" and r["identifier"] == response["identifier"])
		request["response"] = response
		self._messages_events[request["identifier"]].set()
		self.messages_to_wait.remove(request)

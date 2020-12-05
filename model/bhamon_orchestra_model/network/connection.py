import abc


class NetworkConnection(abc.ABC):
	""" Base class for a network connection """

	@property
	@abc.abstractmethod
	def remote_address(self) -> str:
		""" The connection remote address """

	@abc.abstractmethod
	async def ping(self) -> None:
		""" Send a ping """

	@abc.abstractmethod
	async def send(self, data: str) -> None:
		""" Send a message """

	@abc.abstractmethod
	async def receive(self) -> str:
		""" Receive the next message """

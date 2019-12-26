class WebSocketConnection:


	def __init__(self, connection):
		self.connection = connection


	async def ping(self):
		return await self.connection.ping()


	async def send(self, data):
		await self.connection.send(data)


	async def receive(self):
		return await self.connection.recv()

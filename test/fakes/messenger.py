class InProcessMessenger: # pylint: disable = too-few-public-methods
	""" Messenger between two objects in the same process """


	def __init__(self, remote_handler):
		self.remote_handler = remote_handler


	async def send_request(self, data):
		return await self.remote_handler(data)

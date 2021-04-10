import datetime

from bhamon_orchestra_model.date_time_provider import DateTimeProvider


class FakeDateTimeProvider(DateTimeProvider): # pylint: disable = too-few-public-methods
	""" Fake datetime provider for unit tests """


	def __init__(self):
		super().__init__()
		self.now_value = datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc)


	def now(self):
		return self.now_value

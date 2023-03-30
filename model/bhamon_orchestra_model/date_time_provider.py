import datetime


class DateTimeProvider: # pylint: disable = too-few-public-methods
	""" Provider to standardize operations with datetime objects and allow overriding.

	This implementation uses UTC times and limits precision to the second.

	"""


	def now(self) -> datetime.datetime:
		""" Return the current datetime """
		return datetime.datetime.now(datetime.timezone.utc).replace(microsecond = 0)

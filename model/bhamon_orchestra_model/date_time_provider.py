import datetime

import dateutil.parser


class DateTimeProvider:


	def now(self): # pylint: disable = no-self-use
		return datetime.datetime.utcnow().replace(microsecond = 0)


	def serialize(self, value): # pylint: disable = no-self-use
		return value.replace(microsecond = 0, tzinfo = None).isoformat() + "Z"


	def deserialize(self, value): # pylint: disable = no-self-use
		return dateutil.parser.parse(value).replace(microsecond = 0, tzinfo = None)

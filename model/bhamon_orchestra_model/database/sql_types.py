import datetime

import sqlalchemy.types


class UtcDateTime(sqlalchemy.types.TypeDecorator): # pylint: disable = abstract-method


	impl = sqlalchemy.types.DateTime(timezone = True)


	def process_bind_param(self, value, dialect):
		if value is None:
			return None
		if value.tzinfo is None:
			raise ValueError("UtcDateTime value must have timezone information")
		return value.astimezone(datetime.timezone.utc)


	def process_result_value(self, value, dialect):
		if value is None:
			return None
		return value.astimezone(datetime.timezone.utc)

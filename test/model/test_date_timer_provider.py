""" Unit tests for DateTimeProvider """

import datetime

from bhamon_orchestra_model.date_time_provider import DateTimeProvider


def test_serialization():
	""" Test datetime serialization """

	date_time_provider_instance = DateTimeProvider()

	value_as_datetime = datetime.datetime(2020, 1, 1, 0, 0, 0)
	value_as_string = "2020-01-01T00:00:00Z"

	value_serialized = date_time_provider_instance.serialize(value_as_datetime)
	value_deserialized = date_time_provider_instance.deserialize(value_serialized)

	assert value_as_datetime == value_deserialized
	assert value_as_string == value_serialized

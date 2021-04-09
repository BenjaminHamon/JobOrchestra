""" Unit tests for Serializer implementations """

import pytest

from bhamon_orchestra_model.serialization.serializer import Serializer
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer


def list_implementations():
	return [ "json" ]


def instantiate_implementation(implementation: str) -> Serializer:
	if implementation == "json":
		return JsonSerializer(indent = 4)

	raise ValueError("Unsupported implementation '%s'" % implementation)


@pytest.mark.parametrize("implementation", list_implementations())
def test_simple(implementation):
	""" Test serialization with simple values """

	serializer = instantiate_implementation(implementation)

	all_values = [ 1, 1.0, "text" ]

	for value in all_values:
		serialized_value = serializer.serialize_to_string(value)
		deserialized_value = serializer.deserialize_from_string(serialized_value)

		assert deserialized_value == value


@pytest.mark.parametrize("implementation", list_implementations())
def test_collection(implementation):
	""" Test serialization with collections """

	serializer = instantiate_implementation(implementation)

	all_values = [
		[ 1, 2, 3 ],
		{ "first": 1, "second": 2, "third": 3 },
	]

	for value in all_values:
		serialized_value = serializer.serialize_to_string(value)
		deserialized_value = serializer.deserialize_from_string(serialized_value)

		assert deserialized_value == value

""" Unit tests for MemoryDatabaseClient """

import bhamon_build_model.memory_database_client as memory_database_client


def test_single():
	""" Test database client by performing a few operations with a single object """

	client = memory_database_client.MemoryDatabaseClient()
	table = "object"
	obj = { "id": 1, "key": "value" }

	assert client.count(table, {}) == 0

	client.insert_one(table, obj)
	assert client.count(table, {}) == 1

	client.delete_one(table, obj)
	assert client.count(table, {}) == 0


def test_many():
	""" Test database client by performing a few operations with a few objects """

	client = memory_database_client.MemoryDatabaseClient()
	table = "object"

	first_object = { "id": 1, "key": "first" }
	second_object = { "id": 2, "key": "second" }
	third_object = { "id": 3, "key": "third" }

	assert client.count(table, {}) == 0

	client.insert_one(table, first_object)
	client.insert_one(table, second_object)
	client.insert_one(table, third_object)
	assert client.find_many(table, {}) == [ first_object, second_object, third_object ]
	assert client.count(table, {}) == 3

	client.delete_one(table, third_object)
	assert client.find_many(table, {}) == [ first_object, second_object ]
	assert client.count(table, {}) == 2

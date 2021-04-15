""" Unit tests for MemoryDatabaseClient """

from bhamon_orchestra_model.database.memory_database_client import MemoryDatabaseClient


def test_single():
	""" Test database operations with a single record """

	client = MemoryDatabaseClient()
	table = "record"

	record = { "id": 1, "key": "value" }
	record_updated = { "id": 1, "key": "value_updated" }

	assert client.count(table, {}) == 0

	client.insert_one(table, record)
	assert client.count(table, {}) == 1
	assert client.find_one(table, {}) == record

	client.update_one(table, record, record_updated)
	assert client.find_one(table, {}) == record_updated

	client.delete_one(table, record_updated)
	assert client.count(table, {}) == 0


def test_many():
	""" Test database operations with several records """

	client = MemoryDatabaseClient()
	table = "record"

	first_record = { "id": 1, "key": "first" }
	second_record = { "id": 2, "key": "second" }
	third_record = { "id": 3, "key": "third" }

	assert client.count(table, {}) == 0

	client.insert_many(table, [ first_record, second_record, third_record ])
	assert client.find_many(table, {}) == [ first_record, second_record, third_record ]
	assert client.count(table, {}) == 3

	client.delete_one(table, third_record)
	assert client.find_many(table, {}) == [ first_record, second_record ]
	assert client.count(table, {}) == 2

""" Integration tests for database clients """

import pytest

from . import context
from . import environment


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_single(tmpdir, database_type):
	""" Test database operations with a single record """

	table = "record"
	record = { "id": 1, "key": "value" }

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		assert context_instance.database_client.count(table, {}) == 0

		context_instance.database_client.insert_one(table, record)
		assert context_instance.database_client.count(table, {}) == 1

		context_instance.database_client.delete_one(table, record)
		assert context_instance.database_client.count(table, {}) == 0


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_many(tmpdir, database_type):
	""" Test database operations with several records """

	table = "record"
	first_record = { "id": 1, "key": "first" }
	second_record = { "id": 2, "key": "second" }
	third_record = { "id": 3, "key": "third" }

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		assert context_instance.database_client.count(table, {}) == 0

		context_instance.database_client.insert_one(table, first_record)
		context_instance.database_client.insert_one(table, second_record)
		context_instance.database_client.insert_one(table, third_record)
		assert context_instance.database_client.find_many(table, {}) == [ first_record, second_record, third_record ]
		assert context_instance.database_client.count(table, {}) == 3

		context_instance.database_client.delete_one(table, third_record)
		assert context_instance.database_client.find_many(table, {}) == [ first_record, second_record ]
		assert context_instance.database_client.count(table, {}) == 2


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_index(tmpdir, database_type):
	""" Test database operations on a table with an index """

	table = "record"
	record = { "id": 1, "key": "first" }

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		context_instance.database_administration.create_index(table, "id_unique", [ ("id", "ascending") ], is_unique = True)

		assert context_instance.database_client.count(table, {}) == 0

		context_instance.database_client.insert_one(table, record)
		assert context_instance.database_client.count(table, {}) == 1

		with pytest.raises(Exception):
			context_instance.database_client.insert_one(table, record)
		assert context_instance.database_client.count(table, {}) == 1

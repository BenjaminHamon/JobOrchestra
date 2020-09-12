""" Integration tests for database clients """

import os

import pytest

import bhamon_orchestra_model.database.import_export as database_import_export

from . import context
from . import environment


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_single(tmpdir, database_type):
	""" Test database operations with a single record """

	table = "record_simple"
	record = { "id": 1, "key": "value" }

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		with context_instance.database_client_factory() as database_client:

			assert database_client.count(table, {}) == 0

			database_client.insert_one(table, record)
			assert database_client.count(table, {}) == 1
			assert database_client.find_one(table, {}) == record

			database_client.delete_one(table, record)
			assert database_client.find_one(table, {}) is None
			assert database_client.count(table, {}) == 0


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_many(tmpdir, database_type):
	""" Test database operations with several records """

	table = "record_simple"
	first_record = { "id": 1, "key": "first" }
	second_record = { "id": 2, "key": "second" }
	third_record = { "id": 3, "key": "third" }

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		with context_instance.database_client_factory() as database_client:

			assert database_client.count(table, {}) == 0

			database_client.insert_many(table, [ first_record, second_record, third_record ])
			assert database_client.count(table, {}) == 3
			assert database_client.find_many(table, {}) == [ first_record, second_record, third_record ]

			database_client.delete_one(table, third_record)
			assert database_client.count(table, {}) == 2
			assert database_client.find_many(table, {}) == [ first_record, second_record ]


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_find_with_inner_key(tmpdir, database_type):
	""" Test finding a record using an inner key """

	table = "record_document"
	record = { "id": 1, "key": "value", "data": { "inner_key": "inner_value" } }

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		with context_instance.database_client_factory() as database_client:

			assert database_client.count(table, {}) == 0

			database_client.insert_one(table, record)
			assert database_client.count(table, { "data.inner_key": "inner_value" }) == 1
			assert database_client.find_one(table, { "data.inner_key": "inner_value" }) == record


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_order_by(tmpdir, database_type):
	""" Test database operations with order_by options """

	table = "record_simple"

	all_records = [
		{ "id": 1, "key": None },
		{ "id": 2, "key": "ccc" },
		{ "id": 3, "key": None },
		{ "id": 4, "key": "aaa" },
		{ "id": 5, "key": "bbb" },
		{ "id": 6, "key": None },
	]

	sorted_records_ascending = list(sorted(all_records, key = lambda x: (x["key"] is not None, x["key"])))
	sorted_records_descending = list(sorted(all_records, key = lambda x: (x["key"] is not None, x["key"]), reverse = True))

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		with context_instance.database_client_factory() as database_client:

			assert database_client.count(table, {}) == 0

			database_client.insert_many(table, all_records)

			assert database_client.count(table, {}) == len(all_records)
			assert database_client.find_many(table, {}) == all_records
			assert database_client.find_many(table, {}, order_by = ["key"]) == sorted_records_ascending
			assert database_client.find_many(table, {}, order_by = [("key")]) == sorted_records_ascending
			assert database_client.find_many(table, {}, order_by = [("key", "asc")]) == sorted_records_ascending
			assert database_client.find_many(table, {}, order_by = [("key", "ascending")]) == sorted_records_ascending
			assert database_client.find_many(table, {}, order_by = [("key", "desc")]) == sorted_records_descending
			assert database_client.find_many(table, {}, order_by = [("key", "descending")]) == sorted_records_descending


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_order_by_many(tmpdir, database_type):
	""" Test database operations with order_by options """

	table = "record_complex"

	all_records = [
		{ "id": 1, "key_1": "ccc", "key_2": None, "key_3": None },
		{ "id": 2, "key_1": "ccc", "key_2": "aaa", "key_3": None },
		{ "id": 3, "key_1": "aaa", "key_2": "ddd", "key_3": None },
		{ "id": 4, "key_1": "aaa", "key_2": "aaa", "key_3": "aaa" },
		{ "id": 5, "key_1": "bbb", "key_2": None, "key_3": None },
		{ "id": 6, "key_1": "bbb", "key_2": "aaa", "key_3": None },
	]

	order_by = [ ("key_1", "ascending"), ("key_2", "descending"), ("key_3", "ascending") ]

	sorted_records = all_records
	sorted_records = sorted(sorted_records, key = lambda x: (x["key_3"] is not None, x["key_3"]))
	sorted_records = sorted(sorted_records, key = lambda x: (x["key_2"] is not None, x["key_2"]), reverse = True)
	sorted_records = sorted(sorted_records, key = lambda x: (x["key_1"] is not None, x["key_1"]))

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		with context_instance.database_client_factory() as database_client:

			assert database_client.count(table, {}) == 0

			database_client.insert_many(table, all_records)

			assert database_client.count(table, {}) == len(all_records)
			assert database_client.find_many(table, {}) == all_records
			assert database_client.find_many(table, {}, order_by = order_by) == sorted_records


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_order_by_with_inner_key(tmpdir, database_type):
	""" Test ordering records using an inner key """

	table = "record_document"

	all_records = [
		{ "id": 1, "data": { "inner_key": "inner_value_1" } },
		{ "id": 2, "data": { "inner_key": "inner_value_3" } },
		{ "id": 3, "data": { "inner_key": None } },
		{ "id": 4, "data": {} },
		{ "id": 5, "data": { "inner_key": None } },
		{ "id": 6, "data": { "inner_key": "inner_value_2" } },
	]

	sorted_records = sorted(all_records, key = lambda x: (x["data"].get("inner_key", None) is not None, x["data"].get("inner_key", None)))

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		with context_instance.database_client_factory() as database_client:

			assert database_client.count(table, {}) == 0

			database_client.insert_many(table, all_records)

			assert database_client.count(table, {}) == len(all_records)
			assert database_client.find_many(table, {}) == all_records
			assert database_client.find_many(table, {}, order_by = [ "data.inner_key" ]) == sorted_records


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_index(tmpdir, database_type):
	""" Test database operations on a table with an index """

	table = "record_simple"
	first_record = { "id": 1, "key": "first" }
	second_record = { "id": 2, "key": "second" }
	third_record = { "id": 3, "key": "third" }

	with context.DatabaseContext(tmpdir, database_type) as context_instance:
		with context_instance.database_administration_factory() as database_administration:
			database_administration.create_index(table, "id_unique", [ ("id", "ascending") ], is_unique = True)

		with context_instance.database_client_factory() as database_client:

			assert database_client.count(table, {}) == 0

			database_client.insert_one(table, first_record)
			assert database_client.count(table, {}) == 1

			with pytest.raises(Exception):
				database_client.insert_one(table, first_record)
			assert database_client.count(table, {}) == 1

			with pytest.raises(Exception):
				database_client.insert_many(table, [ first_record, second_record, third_record ])
			assert database_client.count(table, {}) == 1


@pytest.mark.parametrize("database_type_source", environment.get_all_database_types())
@pytest.mark.parametrize("database_type_target", environment.get_all_database_types())
def test_import_export(tmpdir, database_type_source, database_type_target):
	""" Test exporting and re-importing a database """

	intermediate_directory = os.path.join(str(tmpdir), "export")

	with context.OrchestraContext(tmpdir, database_type_source, "source") as context_instance:
		with context_instance.database_client_factory() as database_client:
			context_instance.project_provider.create_or_update(database_client, "my-project", None, None)
			context_instance.job_provider.create_or_update(database_client, "my-job", "my-project", None, None, None, None, None, None)
			run = context_instance.run_provider.create(database_client, "my-project", "my-job", None, None)

			database_import_export.export_database(database_client, intermediate_directory)

	with context.OrchestraContext(tmpdir, database_type_target, "target") as context_instance:
		with context_instance.database_client_factory() as database_client:
			database_import_export.import_database(database_client, intermediate_directory)

			assert len(context_instance.project_provider.get_list(database_client)) == 1
			assert context_instance.project_provider.get_list(database_client)[0]["identifier"] == "my-project"
			assert len(context_instance.job_provider.get_list(database_client)) == 1
			assert context_instance.job_provider.get_list(database_client)[0]["identifier"] == "my-job"
			assert len(context_instance.run_provider.get_list(database_client)) == 1
			assert context_instance.run_provider.get_list(database_client)[0]["identifier"] == run["identifier"]

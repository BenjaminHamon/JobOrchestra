""" Integration tests for database administration """

import importlib
import os

import pytest

import bhamon_orchestra_model.database.import_export as database_import_export
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer

from . import context
from . import environment


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_reinitialization(tmpdir, database_type):
	""" Test initializating an already initialized database """

	metadata_factory = lambda: importlib.import_module("bhamon_orchestra_model.database.sql_database_model").metadata

	with context.DatabaseContext(tmpdir, database_type, metadata_factory = metadata_factory) as context_instance:
		with context_instance.database_administration_factory() as database_administration:
			database_administration.initialize()

			with pytest.raises(RuntimeError):
				database_administration.initialize()


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
@pytest.mark.parametrize("base_version", [ "3.0" ])
def test_upgrade(tmpdir, database_type, base_version):
	""" Test upgrading a database """

	if database_type == "json":
		pytest.skip("Unsupported operation")

	metadata_factory = None

	if database_type == "postgresql":
		model_module_name = "bhamon_orchestra_model.database.migrations.sql.model_%s" % base_version.replace(".", "_")
		model_module = importlib.import_module(model_module_name)
		metadata_factory = lambda: model_module.metadata

	with context.DatabaseContext(tmpdir, database_type, metadata_factory = metadata_factory) as context_instance:
		with context_instance.database_administration_factory() as database_administration:
			database_administration.initialize(version = base_version)
			database_administration.upgrade()


@pytest.mark.parametrize("database_type_source", environment.get_all_database_types())
@pytest.mark.parametrize("database_type_target", environment.get_all_database_types())
def test_import_export(tmpdir, database_type_source, database_type_target):
	""" Test exporting and re-importing a database """

	serializer = JsonSerializer(indent = 4)
	intermediate_directory = os.path.join(str(tmpdir), "export")

	with context.OrchestraContext(tmpdir, database_type_source, database_suffix = "source") as context_instance:
		with context_instance.database_client_factory() as database_client:
			context_instance.project_provider.create_or_update(database_client, "my-project", "My Project", {})
			context_instance.job_provider.create_or_update(database_client, "my-job", "my-project", "My Job", "", [], [], {})
			run = context_instance.run_provider.create(database_client, "my-project", "my-job", {}, {})

			database_import_export.export_database(database_client, serializer, intermediate_directory)

	with context.OrchestraContext(tmpdir, database_type_target, database_suffix = "target") as context_instance:
		with context_instance.database_client_factory() as database_client:
			database_import_export.import_database(database_client, serializer, intermediate_directory)

			assert len(context_instance.project_provider.get_list(database_client)) == 1
			assert context_instance.project_provider.get_list(database_client)[0]["identifier"] == "my-project"
			assert len(context_instance.job_provider.get_list(database_client)) == 1
			assert context_instance.job_provider.get_list(database_client)[0]["identifier"] == "my-job"
			assert len(context_instance.run_provider.get_list(database_client)) == 1
			assert context_instance.run_provider.get_list(database_client)[0]["identifier"] == run["identifier"]

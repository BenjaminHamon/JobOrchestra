""" Integration tests for job execution """

import time

import pytest

from .. import assert_extensions
from . import context
from . import environment


log_format = environment.load_environment()["logging_stream_format"]


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_success(tmpdir, database_type):
	""" Test executing a job which should succeed """

	project_identifier = "examples"
	job_identifier = "success"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		with context_instance.database_client_factory() as database_client:
			run = run_and_wait(context_instance.run_provider, database_client, project_identifier, job_identifier)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run '%s' with status succeeded" % run["identifier"] },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status succeeded" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])

	assert run["status"] == "succeeded"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_failure(tmpdir, database_type):
	""" Test executing a job which should fail """

	project_identifier = "examples"
	job_identifier = "failure"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		with context_instance.database_client_factory() as database_client:
			run = run_and_wait(context_instance.run_provider, database_client, project_identifier, job_identifier)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run '%s' with status failed" % run["identifier"] },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status failed" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])

	assert run["status"] == "failed"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_exception(tmpdir, database_type):
	""" Test executing a job which should raise an exception """

	project_identifier = "examples"
	job_identifier = "exception"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		with context_instance.database_client_factory() as database_client:
			run = run_and_wait(context_instance.run_provider, database_client, project_identifier, job_identifier)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run '%s' with status exception" % run["identifier"] },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Error", "logger": "Executor", "message": "(%s) Run raised an exception" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status exception" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])

	assert run["status"] == "exception"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_run_cancel(tmpdir, database_type):
	""" Test cancelling a run """

	project_identifier = "examples"
	job_identifier = "success"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		master_process = context_instance.invoke_master()

		with context_instance.database_client_factory() as database_client:
			run = context_instance.run_provider.create(database_client, project_identifier, job_identifier, {}, None)
			context_instance.run_provider.update_status(database_client, run, should_cancel = True)

			condition_function = lambda: context_instance.run_provider.get(database_client, run["project"], run["identifier"])["status"] not in [ "pending", "running" ]
			assert_extensions.wait_for_condition(condition_function, timeout_seconds = 30)
			time.sleep(2)

			run = context_instance.run_provider.get(database_client, run["project"], run["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "JobScheduler", "message": "Cancelling run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
	])

	assert run["status"] == "cancelled"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_run_abort(tmpdir, database_type):
	""" Test aborting a run """

	project_identifier = "examples"
	job_identifier = "sleep"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		with context_instance.database_client_factory() as database_client:
			run = context_instance.run_provider.create(database_client, project_identifier, job_identifier, {}, None)
			context_instance.run_provider.update_status(database_client, run, should_abort = True)

			condition_function = lambda: context_instance.run_provider.get(database_client, run["project"], run["identifier"])["status"] not in [ "pending", "running" ]
			assert_extensions.wait_for_condition(condition_function, timeout_seconds = 30)
			time.sleep(2)

			run = context_instance.run_provider.get(database_client, run["project"], run["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Aborting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run '%s' with status aborted" % run["identifier"] },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status aborted" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])

	assert run["status"] == "aborted"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_run_without_master(tmpdir, database_type):
	""" Test executing a run without being connected to the master """

	project_identifier = "examples"
	job_identifier = "sleep"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		with context_instance.database_client_factory() as database_client:
			run = context_instance.run_provider.create(database_client, project_identifier, job_identifier, {}, None)

			condition_function = lambda: context_instance.run_provider.get(database_client, run["project"], run["identifier"])["status"] == "running"
			assert_extensions.wait_for_condition(condition_function)
			time.sleep(2)

			run = context_instance.run_provider.get(database_client, run["project"], run["identifier"])

		context_instance.terminate(master_process["identifier"], master_process["process"], "Shutdown")

		time.sleep(5)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run '%s'" % run["identifier"] },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status succeeded" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])

	assert run["status"] == "running"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_run_recovery_on_master(tmpdir, database_type):
	""" Test recovering a run """

	project_identifier = "examples"
	job_identifier = "sleep"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		with context_instance.database_client_factory() as database_client:
			run = context_instance.run_provider.create(database_client, project_identifier, job_identifier, {}, None)

			condition_function = lambda: context_instance.run_provider.get(database_client, run["project"], run["identifier"])["status"] == "running"
			assert_extensions.wait_for_condition(condition_function)

		context_instance.terminate(master_process["identifier"], master_process["process"], "Shutdown")
		master_process = context_instance.invoke_master()

		with context_instance.database_client_factory() as database_client:
			condition_function = lambda: context_instance.run_provider.get(database_client, run["project"], run["identifier"])["status"] not in [ "pending", "running" ]
			assert_extensions.wait_for_condition(condition_function, timeout_seconds = 30)
			time.sleep(2)

			run = context_instance.run_provider.get(database_client, run["project"], run["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Recovering run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run '%s' with status succeeded" % run["identifier"] },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status succeeded" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])

	assert run["status"] == "succeeded"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_run_recovery_on_worker(tmpdir, database_type):
	""" Test recovering a run """

	project_identifier = "examples"
	job_identifier = "sleep"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		with context_instance.database_client_factory() as database_client:
			run = context_instance.run_provider.create(database_client, project_identifier, job_identifier, {}, None)

			condition_function = lambda: context_instance.run_provider.get(database_client, run["project"], run["identifier"])["status"] == "running"
			assert_extensions.wait_for_condition(condition_function)

		context_instance.terminate(worker_process["identifier"], worker_process["process"], "Shutdown")
		worker_process = context_instance.invoke_worker("worker_01")

		with context_instance.database_client_factory() as database_client:
			condition_function = lambda: context_instance.run_provider.get(database_client, run["project"], run["identifier"])["status"] not in [ "pending", "running" ]
			assert_extensions.wait_for_condition(condition_function, timeout_seconds = 30)
			time.sleep(2)

			run = context_instance.run_provider.get(database_client, run["project"], run["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Recovering run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run '%s' with status aborted" % run["identifier"] },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status aborted" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])

	assert run["status"] == "aborted"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_controller_success(tmpdir, database_type):
	""" Test executing a controller job which should succeed """

	project_identifier = "examples"
	job_identifier = "controller_success"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "controller", "worker_01", "worker_02" ])

		master_process = context_instance.invoke_master()
		service_process = context_instance.invoke_service()
		controller_process = context_instance.invoke_worker("controller")
		worker_01_process = context_instance.invoke_worker("worker_01")
		worker_02_process = context_instance.invoke_worker("worker_02")

		with context_instance.database_client_factory() as database_client:
			run = run_and_wait(context_instance.run_provider, database_client, project_identifier, job_identifier)
			all_runs = context_instance.run_provider.get_list(database_client)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed run '%s' with status succeeded" % run["identifier"] },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status succeeded" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
		{ "process": controller_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
	])

	assert run["status"] == "succeeded"
	assert len(all_runs) == 3


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_controller_failure(tmpdir, database_type):
	""" Test executing a controller job which should fail """

	project_identifier = "examples"
	job_identifier = "controller_failure"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "controller", "worker_01", "worker_02" ])

		master_process = context_instance.invoke_master()
		service_process = context_instance.invoke_service()
		controller_process = context_instance.invoke_worker("controller")
		worker_01_process = context_instance.invoke_worker("worker_01")
		worker_02_process = context_instance.invoke_worker("worker_02")

		with context_instance.database_client_factory() as database_client:
			run = run_and_wait(context_instance.run_provider, database_client, project_identifier, job_identifier)
			all_runs = context_instance.run_provider.get_list(database_client)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed run '%s' with status failed" % run["identifier"] },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status failed" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
		{ "process": controller_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
	])

	assert run["status"] == "failed"
	assert len(all_runs) == 3


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_pipeline_success(tmpdir, database_type):
	""" Test executing a pipeline which should succeed """

	project_identifier = "examples"
	job_identifier = "pipeline_success"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "controller", "worker_01", "worker_02" ])

		master_process = context_instance.invoke_master()
		service_process = context_instance.invoke_service()
		controller_process = context_instance.invoke_worker("controller")
		worker_01_process = context_instance.invoke_worker("worker_01")
		worker_02_process = context_instance.invoke_worker("worker_02")

		with context_instance.database_client_factory() as database_client:
			run = run_and_wait(context_instance.run_provider, database_client, project_identifier, job_identifier)
			all_runs = context_instance.run_provider.get_list(database_client)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed run '%s' with status succeeded" % run["identifier"] },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status succeeded" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
		{ "process": controller_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
	])

	assert run["status"] == "succeeded"
	assert len(all_runs) == 5
	assert all(x["status"] == "succeeded" for x in all_runs if x["job"] != run["job"])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_pipeline_failure(tmpdir, database_type):
	""" Test executing a pipeline which should fail """

	project_identifier = "examples"
	job_identifier = "pipeline_failure"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "controller", "worker_01", "worker_02" ])

		master_process = context_instance.invoke_master()
		service_process = context_instance.invoke_service()
		controller_process = context_instance.invoke_worker("controller")
		worker_01_process = context_instance.invoke_worker("worker_01")
		worker_02_process = context_instance.invoke_worker("worker_02")

		with context_instance.database_client_factory() as database_client:
			run = run_and_wait(context_instance.run_provider, database_client, project_identifier, job_identifier)
			all_runs = context_instance.run_provider.get_list(database_client)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed run '%s' with status failed" % run["identifier"] },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status failed" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
		{ "process": controller_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
	])

	assert run["status"] == "failed"
	assert len(all_runs) == 5
	assert all(x["status"] in [ "succeeded", "failed" ] for x in all_runs if x["job"] != run["job"])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_pipeline_exception(tmpdir, database_type): # pylint: disable = too-many-locals
	""" Test executing a pipeline which should raise an exception """

	project_identifier = "examples"
	job_identifier = "pipeline_exception"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "controller", "worker_01", "worker_02" ])

		master_process = context_instance.invoke_master()
		service_process = context_instance.invoke_service()
		controller_process = context_instance.invoke_worker("controller")
		worker_01_process = context_instance.invoke_worker("worker_01")
		worker_02_process = context_instance.invoke_worker("worker_02")

		with context_instance.database_client_factory() as database_client:
			run = run_and_wait(context_instance.run_provider, database_client, project_identifier, job_identifier)
			all_runs = context_instance.run_provider.get_list(database_client)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed run '%s' with status exception" % run["identifier"] },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Error", "logger": "Executor", "message": "(%s) Run raised an exception" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status exception" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	service_expected_messages = [
		{ "level": "Error", "logger": "Request", "message": "(127.0.0.1) POST http://127.0.0.1:5902/project/examples/job/unknown/trigger (StatusCode: 500)" }
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": service_expected_messages },
		{ "process": controller_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
	])

	assert run["status"] == "exception"
	assert len(all_runs) == 3
	assert all(x["status"] == "succeeded" for x in all_runs if x["job"] != run["job"])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_pipeline_abort(tmpdir, database_type): # pylint: disable = too-many-locals
	""" Test executing a pipeline which gets aborted """

	project_identifier = "examples"
	job_identifier = "pipeline_sleep"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "controller", "worker_01", "worker_02" ])

		master_process = context_instance.invoke_master()
		service_process = context_instance.invoke_service()
		controller_process = context_instance.invoke_worker("controller")
		worker_01_process = context_instance.invoke_worker("worker_01")
		worker_02_process = context_instance.invoke_worker("worker_02")

		with context_instance.database_client_factory() as database_client:
			run = context_instance.run_provider.create(database_client, project_identifier, job_identifier, {}, None)
			context_instance.run_provider.update_status(database_client, run, should_abort = True)

			condition_function = lambda: context_instance.run_provider.get(database_client, run["project"], run["identifier"])["status"] not in [ "pending", "running" ]
			assert_extensions.wait_for_condition(condition_function, timeout_seconds = 30)
			time.sleep(2)

			run = context_instance.run_provider.get(database_client, run["project"], run["identifier"])
			all_runs = context_instance.run_provider.get_list(database_client)

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed run '%s' with status aborted" % run["identifier"] },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status aborted" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run '%s'" % run["identifier"] },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
		{ "process": controller_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": [] },
	])

	assert run["status"] == "aborted"
	assert len(all_runs) == 3
	assert all(x["status"] in [ "aborted", "cancelled" ] for x in all_runs if x["job"] != run["job"])


def run_and_wait(run_provider, database_client, project_identifier, job_identifier):
	run = run_provider.create(database_client, project_identifier, job_identifier, {}, None)

	condition_function = lambda: run_provider.get(database_client, run["project"], run["identifier"])["status"] not in [ "pending", "running" ]
	assert_extensions.wait_for_condition(condition_function, timeout_seconds = 30)
	time.sleep(2)

	return run_provider.get(database_client, run["project"], run["identifier"])

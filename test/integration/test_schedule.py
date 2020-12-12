""" Integration tests for schedules """

import time

import pytest

from .. import assert_extensions
from . import context
from . import environment


log_format = environment.load_environment()["logging_stream_format"]


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_schedule(tmpdir, database_type):
	""" Test executing a job which should succeed """

	project_identifier = "examples"
	job_identifier = "success"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		with context_instance.database_client_factory() as database_client:
			schedule = context_instance.schedule_provider.create_or_update(
				database_client, "success_continuous", project_identifier, "Success Continuous", job_identifier, {}, "* * * * *")
			context_instance.schedule_provider.update_status(database_client, schedule, is_enabled = True)

			condition_function = lambda: context_instance.schedule_provider.get(database_client, schedule["project"], schedule["identifier"])["last_run"] is not None
			assert_extensions.wait_for_condition(condition_function)

			context_instance.schedule_provider.update_status(database_client, schedule, is_enabled = False)
			schedule = context_instance.schedule_provider.get(database_client, schedule["project"], schedule["identifier"])
			run = context_instance.run_provider.get(database_client, schedule["project"], schedule["last_run"])

			condition_function = lambda: context_instance.run_provider.get(database_client, run["project"], run["identifier"])["status"] not in [ "pending", "running" ]
			assert_extensions.wait_for_condition(condition_function, timeout_seconds = 30)
			time.sleep(2)

			schedule = context_instance.schedule_provider.get(database_client, schedule["project"], schedule["identifier"])
			run = context_instance.run_provider.get(database_client, schedule["project"], schedule["last_run"])

	master_expected_messages = [
		{ "level": "Info", "logger": "JobScheduler", "message": "Triggering run for schedule '%s'" % schedule["identifier"] },
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

	assert schedule["last_run"] is not None
	assert run["status"] == "succeeded"

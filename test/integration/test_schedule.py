""" Integration tests for schedules """

import time

import pytest

from .. import assert_extensions
from . import context
from . import environment


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_schedule(tmpdir, database_type):
	""" Test executing a job which should succeed """

	project_identifier = "examples"
	job_identifier = "examples_success"

	with context.Context(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		schedule = context_instance.schedule_provider.create_or_update("my_schedule", project_identifier, job_identifier, {}, "* * * * *")
		context_instance.schedule_provider.update_status(schedule, is_enabled = True)

		time.sleep(1)

		context_instance.schedule_provider.update_status(schedule, is_enabled = False)

		time.sleep(5)

		schedule = context_instance.schedule_provider.get(schedule["identifier"])
		run = context_instance.run_provider.get(schedule["last_run"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "JobScheduler", "message": "Triggering run for schedule '%s'" % schedule["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run %s %s" % (job_identifier, run["identifier"]) },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run %s %s with status succeeded" % (job_identifier, run["identifier"]) },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])

	assert schedule["last_run"] is not None
	assert run["status"] == "succeeded"

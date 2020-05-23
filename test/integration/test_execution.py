""" Integration tests for job execution """

import time

import pytest

from .. import assert_extensions
from . import context
from . import environment


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_success(tmpdir, database_type):
	""" Test executing a job which should succeed """

	project_identifier = "examples"
	job_identifier = "success"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		run = context_instance.run_provider.create(project_identifier, job_identifier, {}, None)

		time.sleep(5)

		run = context_instance.run_provider.get(run["project"], run["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run %s with status succeeded" % run["identifier"] },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Info", "logger": "Worker", "message": "Executing run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Starting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status succeeded" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Exiting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
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

		run = context_instance.run_provider.create(project_identifier, job_identifier, {}, None)

		time.sleep(5)

		run = context_instance.run_provider.get(run["project"], run["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run %s with status failed" % run["identifier"] },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Info", "logger": "Worker", "message": "Executing run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Starting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status failed" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Exiting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
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

		run = context_instance.run_provider.create(project_identifier, job_identifier, {}, None)

		time.sleep(5)

		run = context_instance.run_provider.get(run["project"], run["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run %s with status exception" % run["identifier"] },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Info", "logger": "Worker", "message": "Executing run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Starting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Error", "logger": "Executor", "message": "(%s) Step exception raised an exception" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status exception" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Exiting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])

	assert run["status"] == "exception"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_run_cancel(tmpdir, database_type):
	""" Test cancelling a run """

	project_identifier = "examples"
	job_identifier = "success"

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		master_process = context_instance.invoke_master()

		run = context_instance.run_provider.create(project_identifier, job_identifier, {}, None)
		context_instance.run_provider.update_status(run, should_cancel = True)

		time.sleep(2)

		run = context_instance.run_provider.get(run["project"], run["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "JobScheduler", "message": "Cancelling run '%s'" % run["identifier"] },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
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

		run = context_instance.run_provider.create(project_identifier, job_identifier, {}, None)
		context_instance.run_provider.update_status(run, should_abort = True)

		time.sleep(5)

		run = context_instance.run_provider.get(run["project"], run["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Aborting run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed run %s with status aborted" % run["identifier"] },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Info", "logger": "Worker", "message": "Executing run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Starting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status aborted" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Exiting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
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

		run = context_instance.run_provider.create(project_identifier, job_identifier, {}, None)

		time.sleep(10)

		run = context_instance.run_provider.get(run["project"], run["identifier"])
		all_runs = context_instance.run_provider.get_list()

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed run %s with status succeeded" % run["identifier"] },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Info", "logger": "Worker", "message": "Executing run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Starting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status succeeded" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Exiting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
		{ "process": controller_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": [] },
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

		run = context_instance.run_provider.create(project_identifier, job_identifier, {}, None)

		time.sleep(10)

		run = context_instance.run_provider.get(run["project"], run["identifier"])
		all_runs = context_instance.run_provider.get_list()

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed run %s with status failed" % run["identifier"] },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Info", "logger": "Worker", "message": "Executing run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Starting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run is starting for project '%s' and job '%s'" % (run["identifier"], project_identifier, job_identifier) },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Run completed with status failed" % run["identifier"] },
		{ "level": "Info", "logger": "Executor", "message": "(%s) Exiting executor" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Cleaning run %s" % run["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
		{ "process": controller_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": [] },
	])

	assert run["status"] == "failed"
	assert len(all_runs) == 3

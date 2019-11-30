 # pylint: disable = too-many-locals

""" Integration tests for job execution """

import time

import pytest

from .. import assert_extensions
from . import context
from . import environment


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_success(tmpdir, database_type):
	""" Test executing a job which should succeed """

	job_identifier = "test_success"

	with context.Context(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		providers = context_instance.instantiate_providers()
		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		build = providers["build"].create(job_identifier, {})
		task = providers["task"].create("trigger_build", { "build_identifier": build["identifier"] })

		time.sleep(5)

		task = providers["task"].get(task["identifier"])
		build = providers["build"].get(build["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting build master" },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting build %s %s" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed build %s %s with status succeeded" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Master", "message": "Exiting build master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting build worker" },
		{ "level": "Info", "logger": "Worker", "message": "Executing %s %s" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Worker", "message": "Exiting build worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])

	assert task["status"] == "succeeded"
	assert build["status"] == "succeeded"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_failure(tmpdir, database_type):
	""" Test executing a job which should fail """

	job_identifier = "test_failure"

	with context.Context(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		providers = context_instance.instantiate_providers()
		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		build = providers["build"].create(job_identifier, {})
		task = providers["task"].create("trigger_build", { "build_identifier": build["identifier"] })

		time.sleep(5)

		task = providers["task"].get(task["identifier"])
		build = providers["build"].get(build["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting build master" },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting build %s %s" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed build %s %s with status failed" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Master", "message": "Exiting build master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting build worker" },
		{ "level": "Info", "logger": "Worker", "message": "Executing %s %s" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Worker", "message": "Exiting build worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])

	assert task["status"] == "succeeded"
	assert build["status"] == "failed"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_exception(tmpdir, database_type):
	""" Test executing a job which should raise an exception """

	job_identifier = "test_exception"

	with context.Context(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		providers = context_instance.instantiate_providers()
		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		build = providers["build"].create(job_identifier, {})
		task = providers["task"].create("trigger_build", { "build_identifier": build["identifier"] })

		time.sleep(5)

		task = providers["task"].get(task["identifier"])
		build = providers["build"].get(build["identifier"])

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting build master" },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Starting build %s %s" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Worker", "message": "(worker_01) Completed build %s %s with status exception" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Master", "message": "Exiting build master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting build worker" },
		{ "level": "Info", "logger": "Worker", "message": "Executing %s %s" % (job_identifier, build["identifier"]) },
		{ "level": "Error", "logger": "Executor", "message": "(%s) Step exception raised an exception" % build["identifier"] },
		{ "level": "Info", "logger": "Worker", "message": "Exiting build worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])

	assert task["status"] == "succeeded"
	assert build["status"] == "exception"


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_controller_success(tmpdir, database_type):
	""" Test executing a controller job which should succeed """

	job_identifier = "test_controller_success"

	with context.Context(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "controller", "worker_01", "worker_02" ])

		providers = context_instance.instantiate_providers()
		master_process = context_instance.invoke_master()
		service_process = context_instance.invoke_service()
		controller_process = context_instance.invoke_worker("controller")
		worker_01_process = context_instance.invoke_worker("worker_01")
		worker_02_process = context_instance.invoke_worker("worker_02")

		build = providers["build"].create(job_identifier, {})
		task = providers["task"].create("trigger_build", { "build_identifier": build["identifier"] })

		time.sleep(15)

		task = providers["task"].get(task["identifier"])
		build = providers["build"].get(build["identifier"])
		all_tasks = providers["task"].get_list()
		all_builds = providers["build"].get_list()

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting build %s %s" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed build %s %s with status succeeded" % (job_identifier, build["identifier"]) },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing %s %s" % (job_identifier, build["identifier"]) },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
		{ "process": controller_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": [] },
	])

	assert task["status"] == "succeeded"
	assert build["status"] == "succeeded"
	assert len(all_tasks) == 3
	assert len(all_builds) == 3


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_job_controller_failure(tmpdir, database_type):
	""" Test executing a controller job which should fail """

	job_identifier = "test_controller_failure"

	with context.Context(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "controller", "worker_01", "worker_02" ])

		providers = context_instance.instantiate_providers()
		master_process = context_instance.invoke_master()
		service_process = context_instance.invoke_service()
		controller_process = context_instance.invoke_worker("controller")
		worker_01_process = context_instance.invoke_worker("worker_01")
		worker_02_process = context_instance.invoke_worker("worker_02")

		build = providers["build"].create(job_identifier, {})
		task = providers["task"].create("trigger_build", { "build_identifier": build["identifier"] })

		time.sleep(15)

		task = providers["task"].get(task["identifier"])
		build = providers["build"].get(build["identifier"])
		all_tasks = providers["task"].get_list()
		all_builds = providers["build"].get_list()

	master_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "(controller) Starting build %s %s" % (job_identifier, build["identifier"]) },
		{ "level": "Info", "logger": "Worker", "message": "(controller) Completed build %s %s with status failed" % (job_identifier, build["identifier"]) },
	]

	controller_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Executing %s %s" % (job_identifier, build["identifier"]) },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
		{ "process": controller_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": controller_expected_messages },
		{ "process": worker_01_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": [] },
		{ "process": worker_02_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": [] },
	])

	assert task["status"] == "succeeded"
	assert build["status"] == "failed"
	assert len(all_tasks) == 3
	assert len(all_builds) == 3

""" Integration tests for job execution """

import time

import assert_extensions
import context
import environment


def test_job_success(tmpdir):
	""" Execute the job test_success """

	job_identifier = "test_success"

	with context.Context(tmpdir) as context_instance:
		providers = context.instantiate_providers(tmpdir)
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
		{ "identifier": "master", "process": master_process, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "identifier": "worker_01", "process": worker_process, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])

	assert task["status"] == "succeeded"
	assert build["status"] == "succeeded"


def test_job_failure(tmpdir):
	""" Execute the job test_failure """

	job_identifier = "test_failure"

	with context.Context(tmpdir) as context_instance:
		providers = context.instantiate_providers(tmpdir)
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
		{ "identifier": "master", "process": master_process, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "identifier": "worker_01", "process": worker_process, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])

	assert task["status"] == "succeeded"
	assert build["status"] == "failed"


def test_job_exception(tmpdir):
	""" Execute the job test_exception """

	job_identifier = "test_exception"

	with context.Context(tmpdir) as context_instance:
		providers = context.instantiate_providers(tmpdir)
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
		{ "identifier": "master", "process": master_process, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "identifier": "worker_01", "process": worker_process, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])

	assert task["status"] == "succeeded"
	assert build["status"] == "exception"

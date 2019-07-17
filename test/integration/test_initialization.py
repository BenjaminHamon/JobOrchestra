""" Integration tests for initialization """

from .. import assert_extensions
from . import context
from . import environment


def test_master(tmpdir):
	""" Test if the master starts successfully """

	with context.Context(tmpdir) as context_instance:
		master_process = context_instance.invoke_master()

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting build master" },
		{ "level": "Info", "logger": "Master", "message": "Exiting build master" },
	]

	assert_extensions.assert_multi_process([
		{ "identifier": "master", "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
	])


def test_worker(tmpdir):
	""" Test if the worker starts successfully """

	with context.Context(tmpdir) as context_instance:
		worker_process = context_instance.invoke_worker("worker")

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting build worker" },
		{ "level": "Error", "logger": "Worker", "message": "Failed to connect to master" },
		{ "level": "Info", "logger": "Worker", "message": "Exiting build worker" },
	]

	assert_extensions.assert_multi_process([
		{ "identifier": "worker", "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])


def test_executor(tmpdir):
	""" Test if the executor starts successfully """

	with context.Context(tmpdir) as context_instance:
		executor_process = context_instance.invoke_executor("worker", "job", "00000000-0000-0000-0000-000000000000")

	executor_expected_messages = [
		{ "level": "Info", "logger": "Executor", "message": "(00000000-0000-0000-0000-000000000000) Executing job" },
	]

	assert_extensions.assert_multi_process([
		{ "identifier": "executor", "process": executor_process, "expected_result_code": 1, "log_format": environment.log_format, "expected_messages": executor_expected_messages },
	])


def test_service(tmpdir):
	""" Test if the service starts successfully """

	with context.Context(tmpdir) as context_instance:
		service_process = context_instance.invoke_service()

	assert_extensions.assert_multi_process([
		{ "identifier": "service", "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


def test_website(tmpdir):
	""" Test if the website starts successfully """

	with context.Context(tmpdir) as context_instance:
		website_process = context_instance.invoke_website()

	assert_extensions.assert_multi_process([
		{ "identifier": "website", "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])

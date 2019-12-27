""" Integration tests for initialization """

import time

import pytest

from .. import assert_extensions
from . import context
from . import environment


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_master(tmpdir, database_type):
	""" Test if the master starts successfully """

	with context.Context(tmpdir, database_type) as context_instance:
		master_process = context_instance.invoke_master()

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_worker(tmpdir, database_type):
	""" Test if the worker starts successfully """

	with context.Context(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker" ])
		worker_process = context_instance.invoke_worker("worker")

		time.sleep(2) # Wait for the connection to fail

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Error", "logger": "WebSocket", "message": "Failed to connect to master" },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])


def test_executor(tmpdir):
	""" Test if the executor starts successfully """

	with context.Context(tmpdir, None) as context_instance:
		executor_process = context_instance.invoke_executor("worker", "job", "00000000-0000-0000-0000-000000000000")

	executor_expected_messages = [
		{ "level": "Info", "logger": "Executor", "message": "(00000000-0000-0000-0000-000000000000) Executing job" },
	]

	assert_extensions.assert_multi_process([
		{ "process": executor_process, "expected_result_code": 1, "log_format": environment.log_format, "expected_messages": executor_expected_messages },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_service(tmpdir, database_type):
	""" Test if the service starts successfully """

	with context.Context(tmpdir, database_type) as context_instance:
		service_process = context_instance.invoke_service()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


def test_website(tmpdir):
	""" Test if the website starts successfully """

	with context.Context(tmpdir, None) as context_instance:
		website_process = context_instance.invoke_website()

	assert_extensions.assert_multi_process([
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])

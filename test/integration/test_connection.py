""" Integration tests for connection between master and workers """

import os
import time

import pytest

from .. import assert_extensions
from . import context
from . import environment


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_worker_disconnection(tmpdir, database_type):
	""" Test a disconnection initiated by the worker """

	with context.Context(tmpdir, database_type) as context_instance:
		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		os.kill(worker_process.pid, context.shutdown_signal)
		time.sleep(1) # Wait for disconnection
		os.kill(master_process.pid, context.shutdown_signal)

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting build master" },
		{ "level": "Info", "logger": "Supervisor", "message": "Receiving connection" },
		{ "level": "Info", "logger": "Supervisor", "message": "Registering worker 'worker_01'" },
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' is now active" },
		{ "level": "Info", "logger": "Supervisor", "message": "Terminating connection with worker 'worker_01'" },
		{ "level": "Info", "logger": "Master", "message": "Exiting build master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting build worker" },
		{ "level": "Info", "logger": "Worker", "message": "Connected to master, waiting for commands" },
		{ "level": "Info", "logger": "Worker", "message": "Closed connection to master" },
		{ "level": "Info", "logger": "Worker", "message": "Exiting build worker" },
	]

	assert_extensions.assert_multi_process([
		{ "identifier": "master", "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "identifier": "worker_01", "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_master_disconnection(tmpdir, database_type):
	""" Test a disconnection initiated by the master """

	with context.Context(tmpdir, database_type) as context_instance:
		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		os.kill(master_process.pid, context.shutdown_signal)
		time.sleep(1) # Wait for disconnection
		os.kill(worker_process.pid, context.shutdown_signal)

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting build master" },
		{ "level": "Info", "logger": "Supervisor", "message": "Receiving connection" },
		{ "level": "Info", "logger": "Supervisor", "message": "Registering worker 'worker_01'" },
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' is now active" },
		{ "level": "Info", "logger": "Supervisor", "message": "Terminating connection with worker 'worker_01'" },
		{ "level": "Info", "logger": "Master", "message": "Exiting build master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting build worker" },
		{ "level": "Info", "logger": "Worker", "message": "Connected to master, waiting for commands" },
		{ "level": "Info", "logger": "Worker", "message": "Closed connection to master" },
		{ "level": "Info", "logger": "Worker", "message": "Retrying connection in 10 seconds" },
		{ "level": "Info", "logger": "Worker", "message": "Exiting build worker" },
	]

	assert_extensions.assert_multi_process([
		{ "identifier": "master", "process": master_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": master_expected_messages },
		{ "identifier": "worker_01", "process": worker_process, "expected_result_code": 0, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])

""" Integration tests for connection between master and workers """

import os
import time

import pytest

from .. import assert_extensions
from . import context
from . import environment


log_format = environment.load_environment()["logging_stream_format"]


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_worker_disconnection(tmpdir, database_type):
	""" Test a disconnection initiated by the worker """

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		os.kill(worker_process["process"].pid, context.shutdown_signal)

		with context_instance.database_client_factory() as database_client:
			condition_function = lambda: not context_instance.worker_provider.get(database_client, "worker_01")["is_active"]
			assert_extensions.wait_for_condition(condition_function)

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "Supervisor", "message": "Connection from worker 'worker_01' (User: 'worker', RemoteAddress: '127.0.0.1')" },
		{ "level": "Info", "logger": "Supervisor", "message": "Registering worker 'worker_01'" },
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' is now active" },
		{ "level": "Info", "logger": "Supervisor", "message": "Terminating connection with worker 'worker_01'" },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Info", "logger": "WebSocket", "message": "Connected to master" },
		{ "level": "Info", "logger": "WebSocket", "message": "Closed connection to master" },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_master_disconnection(tmpdir, database_type):
	""" Test a disconnection initiated by the master """

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		context_instance.configure_worker_authentication([ "worker_01" ])

		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		os.kill(master_process["process"].pid, context.shutdown_signal)

		with context_instance.database_client_factory() as database_client:
			condition_function = lambda: not context_instance.worker_provider.get(database_client, "worker_01")["is_active"]
			assert_extensions.wait_for_condition(condition_function)

		time.sleep(1)

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting master" },
		{ "level": "Info", "logger": "Supervisor", "message": "Connection from worker 'worker_01' (User: 'worker', RemoteAddress: '127.0.0.1')" },
		{ "level": "Info", "logger": "Supervisor", "message": "Registering worker 'worker_01'" },
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' is now active" },
		{ "level": "Info", "logger": "Supervisor", "message": "Terminating connection with worker 'worker_01'" },
		{ "level": "Info", "logger": "Master", "message": "Exiting master" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting worker" },
		{ "level": "Info", "logger": "WebSocket", "message": "Connected to master" },
		{ "level": "Info", "logger": "WebSocket", "message": "Closed connection to master" },
		{ "level": "Info", "logger": "WebSocket", "message": "Retrying connection in 10 seconds" },
		{ "level": "Info", "logger": "Worker", "message": "Exiting worker" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])

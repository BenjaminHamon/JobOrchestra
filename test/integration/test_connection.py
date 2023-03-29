# pylint: disable = unnecessary-lambda-assignment

""" Integration tests for connection between master and workers """

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

		with context_instance.database_client_factory() as database_client:
			condition_function = lambda: context_instance.worker_provider.get(database_client, "worker_01") is not None
			assert_extensions.wait_for_condition(condition_function)

		context_instance.terminate(worker_process["identifier"], worker_process["process"], "Shutdown")

		with context_instance.database_client_factory() as database_client:
			condition_function = lambda: not context_instance.worker_provider.get(database_client, "worker_01")["is_active"]
			assert_extensions.wait_for_condition(condition_function)

	master_expected_messages = [
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' connected (User: 'worker', RemoteAddress: '127.0.0.1')" },
		{ "level": "Info", "logger": "Supervisor", "message": "Registering worker 'worker_01'" },
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' is now active" },
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' disconnected" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "WebSocket", "message": "Connected to master" },
		{ "level": "Info", "logger": "WebSocket", "message": "Closed connection to master" },
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

		with context_instance.database_client_factory() as database_client:
			condition_function = lambda: context_instance.worker_provider.get(database_client, "worker_01") is not None
			assert_extensions.wait_for_condition(condition_function)

		context_instance.terminate(master_process["identifier"], master_process["process"], "Shutdown")

		with context_instance.database_client_factory() as database_client:
			condition_function = lambda: not context_instance.worker_provider.get(database_client, "worker_01")["is_active"]
			assert_extensions.wait_for_condition(condition_function)

	master_expected_messages = [
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' connected (User: 'worker', RemoteAddress: '127.0.0.1')" },
		{ "level": "Info", "logger": "Supervisor", "message": "Registering worker 'worker_01'" },
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' is now active" },
		{ "level": "Info", "logger": "Supervisor", "message": "Worker 'worker_01' disconnected" },
	]

	worker_expected_messages = [
		{ "level": "Info", "logger": "WebSocket", "message": "Connected to master" },
		{ "level": "Info", "logger": "WebSocket", "message": "Closed connection to master" },
		{ "level": "Info", "logger": "WebSocket", "message": "Retrying connection in 10 seconds" },
	]

	assert_extensions.assert_multi_process([
		{ "process": master_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": master_expected_messages },
		{ "process": worker_process, "expected_result_code": 0, "log_format": log_format, "expected_messages": worker_expected_messages },
	])

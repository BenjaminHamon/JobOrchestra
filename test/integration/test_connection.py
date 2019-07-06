""" Integration tests for connection between master and workers """

import os
import time

from .. import assert_extensions
from . import context
from . import environment


def test_worker_disconnection(tmpdir):
	""" Start master then worker, stop worker then master """

	with context.Context(tmpdir) as context_instance:
		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		os.kill(worker_process.pid, context.shutdown_signal)
		time.sleep(1) # Wait for disconnection
		os.kill(master_process.pid, context.shutdown_signal)

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting build master" },
		{ "level": "Info", "logger": "Supervisor", "message": "Accepted connection from worker worker_01" },
		{ "level": "Info", "logger": "Supervisor", "message": "Terminating connection with worker worker_01" },
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


def test_master_disconnection(tmpdir):
	""" Start master then worker, stop master then worker """

	with context.Context(tmpdir) as context_instance:
		master_process = context_instance.invoke_master()
		worker_process = context_instance.invoke_worker("worker_01")

		os.kill(master_process.pid, context.shutdown_signal)
		time.sleep(1) # Wait for disconnection
		os.kill(worker_process.pid, context.shutdown_signal)

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting build master" },
		{ "level": "Info", "logger": "Supervisor", "message": "Accepted connection from worker worker_01" },
		{ "level": "Info", "logger": "Supervisor", "message": "Terminating connection with worker worker_01" },
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

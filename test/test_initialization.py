""" Integration tests for initialization """

import assert_extensions
import context
import environment


def test_master(tmpdir):
	""" Start master """

	with context.Context(tmpdir) as context_instance:
		master_process = context_instance.invoke_master()

	master_expected_messages = [
		{ "level": "Info", "logger": "Master", "message": "Starting build master" },
		{ "level": "Info", "logger": "Master", "message": "Exiting build master" },
	]

	assert_extensions.assert_multi_process([
		{ "identifier": "master", "process": master_process, "log_format": environment.log_format, "expected_messages": master_expected_messages },
	])


def test_worker(tmpdir):
	""" Start worker """

	with context.Context(tmpdir) as context_instance:
		worker_process = context_instance.invoke_worker("worker_01")

	worker_expected_messages = [
		{ "level": "Info", "logger": "Worker", "message": "Starting build worker" },
		{ "level": "Error", "logger": "Worker", "message": "Failed to connect to master" },
		{ "level": "Info", "logger": "Worker", "message": "Exiting build worker" },
	]

	assert_extensions.assert_multi_process([
		{ "identifier": "worker_01", "process": worker_process, "log_format": environment.log_format, "expected_messages": worker_expected_messages },
	])


def test_service(tmpdir):
	""" Start service """

	with context.Context(tmpdir) as context_instance:
		service_process = context_instance.invoke_service()

	service_expected_messages = [
		{ "level": "Info", "logger": "Service", "message": "Starting build master service" },
	]

	assert_extensions.assert_multi_process([
		{ "identifier": "service", "process": service_process, "log_format": environment.log_format, "expected_messages": service_expected_messages },
	])

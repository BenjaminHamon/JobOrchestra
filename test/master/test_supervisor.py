# pylint: disable = protected-access

""" Unit tests for Supervisor """

from bhamon_build_model.build_provider import BuildProvider
from bhamon_build_model.memory_database_client import MemoryDatabaseClient
from bhamon_build_master.supervisor import Supervisor
from bhamon_build_master.worker import Worker


def test_cancel_build_pending():
	""" Test cancelling a pending build """

	database_client_instance = MemoryDatabaseClient()
	build_provider_instance = BuildProvider(database_client_instance, None)

	supervisor_instance = Supervisor(
		host = None,
		port = None,
		build_provider = build_provider_instance,
		job_provider = None,
		worker_provider = None,
		worker_selector = None,
	)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})

	assert build["status"] == "pending"

	operation_result = supervisor_instance.cancel_build(build["identifier"])

	assert operation_result is True
	assert build["status"] == "cancelled"


def test_cancel_build_running():
	""" Test cancelling a running build """

	database_client_instance = MemoryDatabaseClient()
	build_provider_instance = BuildProvider(database_client_instance, None)

	supervisor_instance = Supervisor(
		host = None,
		port = None,
		build_provider = build_provider_instance,
		job_provider = None,
		worker_provider = None,
		worker_selector = None,
	)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})
	build_provider_instance.update_status(build, status = "running")

	assert build["status"] == "running"

	operation_result = supervisor_instance.cancel_build(build["identifier"])

	assert operation_result is False
	assert build["status"] == "running"


def test_cancel_build_completed():
	""" Test cancelling a completed build """

	database_client_instance = MemoryDatabaseClient()
	build_provider_instance = BuildProvider(database_client_instance, None)

	supervisor_instance = Supervisor(
		host = None,
		port = None,
		build_provider = build_provider_instance,
		job_provider = None,
		worker_provider = None,
		worker_selector = None,
	)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})
	build_provider_instance.update_status(build, status = "succeeded")

	assert build["status"] == "succeeded"

	operation_result = supervisor_instance.cancel_build(build["identifier"])

	assert operation_result is False
	assert build["status"] == "succeeded"


def test_abort_build_pending():
	""" Test aborting a pending build """

	database_client_instance = MemoryDatabaseClient()
	build_provider_instance = BuildProvider(database_client_instance, None)

	supervisor_instance = Supervisor(
		host = None,
		port = None,
		build_provider = build_provider_instance,
		job_provider = None,
		worker_provider = None,
		worker_selector = None,
	)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})

	assert build["status"] == "pending"
	assert len(supervisor_instance._active_workers) == 0

	operation_result = supervisor_instance.abort_build(build["identifier"])

	assert operation_result is False
	assert build["status"] == "pending"


def test_abort_build_running_connected():
	""" Test aborting a running build on a connected worker """

	database_client_instance = MemoryDatabaseClient()
	build_provider_instance = BuildProvider(database_client_instance, None)
	worker_instance = Worker("worker_test", None, build_provider_instance)

	supervisor_instance = Supervisor(
		host = None,
		port = None,
		build_provider = build_provider_instance,
		job_provider = None,
		worker_provider = None,
		worker_selector = None,
	)

	supervisor_instance._active_workers[worker_instance.identifier] = worker_instance

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})
	worker_instance.assign_build(job, build)
	build_provider_instance.update_status(build, status = "running")

	assert build["status"] == "running"
	assert build["worker"] == worker_instance.identifier
	assert len(supervisor_instance._active_workers) == 1
	assert len(worker_instance.executors) == 1

	operation_result = supervisor_instance.abort_build(build["identifier"])

	assert operation_result is True
	assert build["status"] == "running"
	assert worker_instance.executors[0]["should_abort"] is True


def test_abort_build_running_disconnected():
	""" Test aborting a running build on a disconnected worker """

	database_client_instance = MemoryDatabaseClient()
	build_provider_instance = BuildProvider(database_client_instance, None)
	worker_instance = Worker("worker_test", None, build_provider_instance)

	supervisor_instance = Supervisor(
		host = None,
		port = None,
		build_provider = build_provider_instance,
		job_provider = None,
		worker_provider = None,
		worker_selector = None,
	)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})
	worker_instance.assign_build(job, build)
	build_provider_instance.update_status(build, status = "running")

	assert build["status"] == "running"
	assert build["worker"] == worker_instance.identifier
	assert len(supervisor_instance._active_workers) == 0
	assert len(worker_instance.executors) == 1

	operation_result = supervisor_instance.abort_build(build["identifier"])

	assert operation_result is False
	assert build["status"] == "running"
	assert worker_instance.executors[0]["should_abort"] is False


def test_abort_build_completed():
	""" Test aborting a completed build """

	database_client_instance = MemoryDatabaseClient()
	build_provider_instance = BuildProvider(database_client_instance, None)

	supervisor_instance = Supervisor(
		host = None,
		port = None,
		build_provider = build_provider_instance,
		job_provider = None,
		worker_provider = None,
		worker_selector = None,
	)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})
	build_provider_instance.update_status(build, status = "succeeded")

	assert build["status"] == "succeeded"
	assert len(supervisor_instance._active_workers) == 0

	operation_result = supervisor_instance.abort_build(build["identifier"])

	assert operation_result is False
	assert build["status"] == "succeeded"

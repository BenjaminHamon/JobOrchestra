""" Unit tests for Supervisor """

from bhamon_build_model.build_provider import BuildProvider
from bhamon_build_model.memory_database_client import MemoryDatabaseClient
from bhamon_build_master.supervisor import Supervisor


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

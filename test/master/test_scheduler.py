# pylint: disable = protected-access

""" Unit tests for JobScheduler """

from bhamon_build_master.job_scheduler import JobScheduler
from bhamon_build_master.supervisor import Supervisor
from bhamon_build_master.worker import Worker
from bhamon_build_model.database.memory_database_client import MemoryDatabaseClient
from bhamon_build_model.run_provider import RunProvider


def test_cancel_run_pending():
	""" Test cancelling a pending run """

	database_client_instance = MemoryDatabaseClient()
	run_provider_instance = RunProvider(database_client_instance, None)
	job_scheduler_instance = JobScheduler(None, None, run_provider_instance, None)

	job = { "identifier": "job_test" }
	run = run_provider_instance.create(job["identifier"], {})

	assert run["status"] == "pending"

	operation_result = job_scheduler_instance.cancel_run(run["identifier"])

	assert operation_result is True
	assert run["status"] == "cancelled"


def test_cancel_run_running():
	""" Test cancelling an in progress run """

	database_client_instance = MemoryDatabaseClient()
	run_provider_instance = RunProvider(database_client_instance, None)
	job_scheduler_instance = JobScheduler(None, None, run_provider_instance, None)

	job = { "identifier": "job_test" }
	run = run_provider_instance.create(job["identifier"], {})
	run_provider_instance.update_status(run, status = "running")

	assert run["status"] == "running"

	operation_result = job_scheduler_instance.cancel_run(run["identifier"])

	assert operation_result is False
	assert run["status"] == "running"


def test_cancel_run_completed():
	""" Test cancelling a completed run """

	database_client_instance = MemoryDatabaseClient()
	run_provider_instance = RunProvider(database_client_instance, None)
	job_scheduler_instance = JobScheduler(None, None, run_provider_instance, None)

	job = { "identifier": "job_test" }
	run = run_provider_instance.create(job["identifier"], {})
	run_provider_instance.update_status(run, status = "succeeded")

	assert run["status"] == "succeeded"

	operation_result = job_scheduler_instance.cancel_run(run["identifier"])

	assert operation_result is False
	assert run["status"] == "succeeded"


def test_abort_run_pending():
	""" Test aborting a pending run """

	database_client_instance = MemoryDatabaseClient()
	run_provider_instance = RunProvider(database_client_instance, None)
	supervisor_instance = Supervisor(None, None, None, None, None, None, None)
	job_scheduler_instance = JobScheduler(supervisor_instance, None, run_provider_instance, None)

	job = { "identifier": "job_test" }
	run = run_provider_instance.create(job["identifier"], {})

	assert run["status"] == "pending"
	assert len(supervisor_instance._active_workers) == 0

	operation_result = job_scheduler_instance.abort_run(run["identifier"])

	assert operation_result is False
	assert run["status"] == "pending"


def test_abort_run_running_connected():
	""" Test aborting an in progress run on a connected worker """

	database_client_instance = MemoryDatabaseClient()
	run_provider_instance = RunProvider(database_client_instance, None)
	worker_instance = Worker("worker_test", None, run_provider_instance)
	supervisor_instance = Supervisor(None, None, None, None, None, None, None)
	job_scheduler_instance = JobScheduler(supervisor_instance, None, run_provider_instance, None)

	supervisor_instance._active_workers[worker_instance.identifier] = worker_instance

	job = { "identifier": "job_test" }
	run = run_provider_instance.create(job["identifier"], {})
	worker_instance.assign_run(job, run)
	run_provider_instance.update_status(run, status = "running")

	assert run["status"] == "running"
	assert run["worker"] == worker_instance.identifier
	assert len(supervisor_instance._active_workers) == 1
	assert len(worker_instance.executors) == 1

	operation_result = job_scheduler_instance.abort_run(run["identifier"])

	assert operation_result is True
	assert run["status"] == "running"
	assert worker_instance.executors[0]["should_abort"] is True


def test_abort_run_running_disconnected():
	""" Test aborting an in progress run on a disconnected worker """

	database_client_instance = MemoryDatabaseClient()
	run_provider_instance = RunProvider(database_client_instance, None)
	worker_instance = Worker("worker_test", None, run_provider_instance)
	supervisor_instance = Supervisor(None, None, None, None, None, None, None)
	job_scheduler_instance = JobScheduler(supervisor_instance, None, run_provider_instance, None)

	job = { "identifier": "job_test" }
	run = run_provider_instance.create(job["identifier"], {})
	worker_instance.assign_run(job, run)
	run_provider_instance.update_status(run, status = "running")

	assert run["status"] == "running"
	assert run["worker"] == worker_instance.identifier
	assert len(supervisor_instance._active_workers) == 0
	assert len(worker_instance.executors) == 1

	operation_result = job_scheduler_instance.abort_run(run["identifier"])

	assert operation_result is False
	assert run["status"] == "running"
	assert worker_instance.executors[0]["should_abort"] is False


def test_abort_run_completed():
	""" Test aborting a completed run """

	database_client_instance = MemoryDatabaseClient()
	run_provider_instance = RunProvider(database_client_instance, None)
	supervisor_instance = Supervisor(None, None, None, None, None, None, None)
	job_scheduler_instance = JobScheduler(supervisor_instance, None, run_provider_instance, None)

	job = { "identifier": "job_test" }
	run = run_provider_instance.create(job["identifier"], {})
	run_provider_instance.update_status(run, status = "succeeded")

	assert run["status"] == "succeeded"
	assert len(supervisor_instance._active_workers) == 0

	operation_result = job_scheduler_instance.abort_run(run["identifier"])

	assert operation_result is False
	assert run["status"] == "succeeded"

# pylint: disable = protected-access

""" Unit tests for JobScheduler """

import pytest

from bhamon_orchestra_master.job_scheduler import JobScheduler
from bhamon_orchestra_master.supervisor import Supervisor
from bhamon_orchestra_master.worker import Worker
from bhamon_orchestra_model.database.memory_database_client import MemoryDatabaseClient
from bhamon_orchestra_model.run_provider import RunProvider

from ..fakes.fake_date_time_provider import FakeDateTimeProvider


def test_abort_run_pending():
	""" Test aborting a pending run """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(database_client_instance, None, date_time_provider_instance)
	supervisor_instance = Supervisor(None, None, None, None, None)
	job_scheduler_instance = JobScheduler(None, run_provider_instance, None, supervisor_instance, None, date_time_provider_instance)

	job = { "project": "examples", "identifier": "empty" }
	run = run_provider_instance.create(job["project"], job["identifier"], {}, None)

	assert run["status"] == "pending"
	assert len(supervisor_instance._active_workers) == 0

	with pytest.raises(ValueError):
		job_scheduler_instance.abort_run(run)

	assert run["status"] == "pending"


def test_abort_run_running_connected():
	""" Test aborting an in progress run on a connected worker """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(database_client_instance, None, date_time_provider_instance)
	worker_instance = Worker("worker_test", None, run_provider_instance)
	supervisor_instance = Supervisor(None, None, None, None, None)
	job_scheduler_instance = JobScheduler(None, run_provider_instance, None, supervisor_instance, None, date_time_provider_instance)

	supervisor_instance._active_workers[worker_instance.identifier] = worker_instance

	job = { "project": "examples", "identifier": "empty" }
	run = run_provider_instance.create(job["project"], job["identifier"], {}, None)
	worker_instance.assign_run(job, run)
	run_provider_instance.update_status(run, status = "running")

	assert run["status"] == "running"
	assert run["worker"] == worker_instance.identifier
	assert len(supervisor_instance._active_workers) == 1
	assert len(worker_instance.executors) == 1

	operation_result = job_scheduler_instance.abort_run(run)

	assert operation_result is True
	assert run["status"] == "running"
	assert worker_instance.executors[0]["should_abort"] is True


def test_abort_run_running_disconnected():
	""" Test aborting an in progress run on a disconnected worker """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(database_client_instance, None, date_time_provider_instance)
	worker_instance = Worker("worker_test", None, run_provider_instance)
	supervisor_instance = Supervisor(None, None, None, None, None)
	job_scheduler_instance = JobScheduler(None, run_provider_instance, None, supervisor_instance, None, date_time_provider_instance)

	job = { "project": "examples", "identifier": "empty" }
	run = run_provider_instance.create(job["project"], job["identifier"], {}, None)
	worker_instance.assign_run(job, run)
	run_provider_instance.update_status(run, status = "running")

	assert run["status"] == "running"
	assert run["worker"] == worker_instance.identifier
	assert len(supervisor_instance._active_workers) == 0
	assert len(worker_instance.executors) == 1

	operation_result = job_scheduler_instance.abort_run(run)

	assert operation_result is False
	assert run["status"] == "running"
	assert worker_instance.executors[0]["should_abort"] is False


def test_abort_run_completed():
	""" Test aborting a completed run """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(database_client_instance, None, date_time_provider_instance)
	supervisor_instance = Supervisor(None, None, None, None, None)
	job_scheduler_instance = JobScheduler(None, run_provider_instance, None, supervisor_instance, None, date_time_provider_instance)

	job = { "project": "examples", "identifier": "empty" }
	run = run_provider_instance.create(job["project"], job["identifier"], {}, None)
	run_provider_instance.update_status(run, status = "succeeded")

	assert run["status"] == "succeeded"
	assert len(supervisor_instance._active_workers) == 0

	with pytest.raises(ValueError):
		job_scheduler_instance.abort_run(run)

	assert run["status"] == "succeeded"

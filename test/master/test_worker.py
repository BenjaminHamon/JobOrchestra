 # pylint: disable = protected-access

""" Unit tests for Worker """

import pytest

from bhamon_orchestra_model.database.memory_database_client import MemoryDatabaseClient
from bhamon_orchestra_model.database.memory_file_storage import MemoryFileStorage
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_master.worker import Worker

from ..fakes.fake_date_time_provider import FakeDateTimeProvider
from ..fakes.fake_run_provider import FakeRunProvider
from ..fakes.mock_worker_remote import MockMessenger, MockWorkerRemote


@pytest.mark.asyncio
async def test_start_execution_success():
	""" Test _start_execution in normal conditions """

	run_provider_instance = FakeRunProvider()
	worker_remote_instance = MockWorkerRemote("worker_test")
	worker_messenger = MockMessenger(worker_remote_instance.handle_request)
	worker_local_instance = Worker("worker_test", worker_messenger, run_provider_instance)

	job = { "identifier": "job_test" }
	run = { "identifier": "run_test", "job": job["identifier"], "status": "pending", "parameters": {} }
	await worker_local_instance._start_execution(run, job)


@pytest.mark.asyncio
async def test_abort_execution_success():
	""" Test _abort_execution in normal conditions """

	run_provider_instance = FakeRunProvider()
	worker_remote_instance = MockWorkerRemote("worker_test")
	worker_messenger = MockMessenger(worker_remote_instance.handle_request)
	worker_local_instance = Worker("worker_test", worker_messenger, run_provider_instance)

	job = { "identifier": "job_test" }
	run = { "identifier": "run_test", "job": job["identifier"], "status": "running", "steps": [] }
	executor = { "job_identifier": job["identifier"], "run_identifier": run["identifier"] }
	executor["status"] = { "status": "running", "steps": [] }

	worker_remote_instance.executors.append(executor)
	await worker_local_instance._abort_execution(run)


@pytest.mark.asyncio
async def test_finish_execution_success():
	""" Test _finish_execution in normal conditions """

	run_provider_instance = FakeRunProvider()
	worker_remote_instance = MockWorkerRemote("worker_test")
	worker_messenger = MockMessenger(worker_remote_instance.handle_request)
	worker_local_instance = Worker("worker_test", worker_messenger, run_provider_instance)

	job = { "identifier": "job_test" }
	run = { "identifier": "run_test", "job": job["identifier"], "status": "succeeded", "steps": [] }
	executor = { "job_identifier": job["identifier"], "run_identifier": run["identifier"] }
	executor["status"] = { "status": "succeeded", "steps": [] }

	worker_remote_instance.executors.append(executor)
	await worker_local_instance._finish_execution(run)


@pytest.mark.asyncio
async def test_process_success():
	""" Test running a run which succeeds """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(database_client_instance, file_storage_instance, date_time_provider_instance)
	worker_remote_instance = MockWorkerRemote("worker_test")
	worker_messenger = MockMessenger(worker_remote_instance.handle_request)
	worker_local_instance = Worker("worker_test", worker_messenger, run_provider_instance)

	job = { "project": "examples", "identifier": "empty" }
	run = run_provider_instance.create(job["project"], job["identifier"], {})

	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_run(job, run)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"

	remote_executor = worker_remote_instance.find_executor(run["identifier"])
	remote_executor["status"]["status"] = "running"

	await worker_local_instance.handle_update({ "run": run["identifier"], "status": remote_executor["status"] })

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	remote_executor["status"]["status"] = "succeeded"
	for step in remote_executor["status"]["steps"]:
		step["status"] = "succeeded"

	await worker_local_instance.handle_update({ "run": run["identifier"], "status": remote_executor["status"] })

	assert local_executor["local_status"] == "running"
	assert run["status"] == "succeeded"

	# running => verifying
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "succeeded"

	await worker_local_instance.handle_update({ "run": run["identifier"], "event": "synchronization_completed" })

	# verifying => finishing
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "succeeded"

	# finishing => done (_finish_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1


@pytest.mark.asyncio
async def test_process_abort():
	""" Test running a run which gets aborted """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(database_client_instance, file_storage_instance, date_time_provider_instance)
	worker_remote_instance = MockWorkerRemote("worker_test")
	worker_messenger = MockMessenger(worker_remote_instance.handle_request)
	worker_local_instance = Worker("worker_test", worker_messenger, run_provider_instance)

	job = { "project": "examples", "identifier": "empty" }
	run = run_provider_instance.create(job["project"], job["identifier"], {})

	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_run(job, run)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"

	remote_executor = worker_remote_instance.find_executor(run["identifier"])
	remote_executor["status"]["status"] = "running"

	await worker_local_instance.handle_update({ "run": run["identifier"], "status": remote_executor["status"] })

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	worker_local_instance.abort_run(run["identifier"])

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	# running => aborting (_abort_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "aborting"
	assert run["status"] == "running"

	await worker_local_instance.handle_update({ "run": run["identifier"], "status": remote_executor["status"] })

	assert local_executor["local_status"] == "aborting"
	assert run["status"] == "aborted"

	# aborting => verifying
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "aborted"

	await worker_local_instance.handle_update({ "run": run["identifier"], "event": "synchronization_completed" })

	# verifying => finishing
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "aborted"

	# finishing => done (_finish_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "aborted"
	assert len(worker_local_instance.executors) == 1


@pytest.mark.asyncio
async def test_process_recovery_during_execution(): # pylint: disable = too-many-statements
	""" Test running a run which gets recovered after a disconnection and while it is running """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(database_client_instance, file_storage_instance, date_time_provider_instance)
	worker_remote_instance = MockWorkerRemote("worker_test")
	worker_messenger = MockMessenger(worker_remote_instance.handle_request)
	worker_local_instance = Worker("worker_test", worker_messenger, run_provider_instance)

	job = { "project": "examples", "identifier": "empty" }
	run = run_provider_instance.create(job["project"], job["identifier"], {})

	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_run(job, run)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	remote_executor = worker_remote_instance.find_executor(run["identifier"])
	remote_executor["status"]["status"] = "running"

	await worker_local_instance.handle_update({ "run": run["identifier"], "status": remote_executor["status"] })

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 1

	# New worker to simulate disconnection
	worker_local_instance = Worker("worker_test", worker_messenger, run_provider_instance)

	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 0

	# none => running (_recover_execution)
	worker_local_instance.executors = await worker_local_instance._recover_executors()
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 1

	await worker_local_instance.handle_update({ "run": run["identifier"], "status": remote_executor["status"] })

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	remote_executor["status"]["status"] = "succeeded"
	for step in remote_executor["status"]["steps"]:
		step["status"] = "succeeded"

	await worker_local_instance.handle_update({ "run": run["identifier"], "status": remote_executor["status"] })

	assert local_executor["local_status"] == "running"
	assert run["status"] == "succeeded"

	# running => verifying
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "succeeded"

	await worker_local_instance.handle_update({ "run": run["identifier"], "event": "synchronization_completed" })

	# verifying => finishing
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "succeeded"

	# finishing => done (_finish_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1


@pytest.mark.asyncio
async def test_process_recovery_after_execution():
	""" Test running a run which gets recovered after a disconnection and after it completed """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(database_client_instance, file_storage_instance, date_time_provider_instance)
	worker_remote_instance = MockWorkerRemote("worker_test")
	worker_messenger = MockMessenger(worker_remote_instance.handle_request)
	worker_local_instance = Worker("worker_test", worker_messenger, run_provider_instance)

	job = { "project": "examples", "identifier": "empty" }
	run = run_provider_instance.create(job["project"], job["identifier"], {})

	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_run(job, run)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	remote_executor = worker_remote_instance.find_executor(run["identifier"])
	remote_executor["status"]["status"] = "running"

	await worker_local_instance.handle_update({ "run": run["identifier"], "status": remote_executor["status"] })

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 1

	# New worker to simulate disconnection
	worker_local_instance = Worker("worker_test", worker_messenger, run_provider_instance)

	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 0

	remote_executor["status"]["status"] = "succeeded"
	for step in remote_executor["status"]["steps"]:
		step["status"] = "succeeded"

	# none => running (_recover_execution)
	worker_local_instance.executors = await worker_local_instance._recover_executors()
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	await worker_local_instance.handle_update({ "run": run["identifier"], "status": remote_executor["status"] })

	assert local_executor["local_status"] == "running"
	assert run["status"] == "succeeded"

	# running => verifying
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "succeeded"

	await worker_local_instance.handle_update({ "run": run["identifier"], "event": "synchronization_completed" })

	# verifying => finishing
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "succeeded"

	# finishing => done (_finish_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1

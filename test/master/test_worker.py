 # pylint: disable = protected-access

""" Unit tests for Worker """

from unittest.mock import Mock

import pytest

from bhamon_orchestra_model.database.memory_database_client import MemoryDatabaseClient
from bhamon_orchestra_model.database.memory_data_storage import MemoryDataStorage
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_master.worker import Worker as LocalWorker
from bhamon_orchestra_worker.executor_watcher import ExecutorWatcher
from bhamon_orchestra_worker.worker import Worker as RemoteWorker
from bhamon_orchestra_worker.worker_storage import WorkerStorage

from ..fakes.executor_watcher import FakeExecutorWatcher
from ..fakes.fake_date_time_provider import FakeDateTimeProvider
from ..fakes.messenger import InProcessMessenger


class FakeRemoteWorker(RemoteWorker): # pylint: disable = too-few-public-methods


	def __init__(self, storage: WorkerStorage) -> None:
		super().__init__(storage, None, None, None, None)


	def _resynchronize(self, run_identifier: str, log_cursor: int) -> None:
		pass


	def _instantiate_executor(self, run_identifier: str) -> ExecutorWatcher:
		return FakeExecutorWatcher(run_identifier)


@pytest.mark.asyncio
async def test_start_execution_success():
	""" Test _start_execution in normal conditions """

	run_provider_instance = Mock(spec = RunProvider)
	worker_storage_instance = Mock(spec = WorkerStorage)

	worker_remote_instance = FakeRemoteWorker(worker_storage_instance)
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: None, run_provider_instance, None)

	job = { "project": "my_project", "identifier": "my_job" }
	run = { "project": "my_project", "identifier": "my_run", "job": "my_job", "status": "pending", "parameters": {} }

	await worker_local_instance._start_execution(run, job)


@pytest.mark.asyncio
async def test_abort_execution_success():
	""" Test _abort_execution in normal conditions """

	run_provider_instance = Mock(spec = RunProvider)
	worker_storage_instance = Mock(spec = WorkerStorage)

	worker_remote_instance = FakeRemoteWorker(worker_storage_instance)
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: None, run_provider_instance, None)

	run = { "project": "my_project", "identifier": "my_run", "job": "my_job", "status": "running", "steps": [] }

	worker_remote_instance._active_executors.append(FakeExecutorWatcher(run["identifier"]))

	await worker_local_instance._abort_execution(run)


@pytest.mark.asyncio
async def test_finish_execution_success():
	""" Test _finish_execution in normal conditions """

	run_provider_instance = Mock(spec = RunProvider)
	worker_storage_instance = Mock(spec = WorkerStorage)

	worker_remote_instance = FakeRemoteWorker(worker_storage_instance)
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: None, run_provider_instance, None)

	run = { "project": "my_project", "identifier": "my_run", "job": "my_job", "status": "succeeded", "steps": [] }

	worker_remote_instance._active_executors.append(FakeExecutorWatcher(run["identifier"]))

	await worker_local_instance._finish_execution(run)


@pytest.mark.asyncio
async def test_process_success():
	""" Test executing a run which succeeds """

	database_client_instance = MemoryDatabaseClient()
	data_storage_instance = MemoryDataStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	worker_storage_instance = Mock(spec = WorkerStorage)

	run_provider_instance = RunProvider(data_storage_instance, date_time_provider_instance)
	worker_remote_instance = FakeRemoteWorker(worker_storage_instance)
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance, None)

	job = { "project": "my_project", "identifier": "my_job" }
	run = run_provider_instance.create(database_client_instance, job["project"], job["identifier"], {}, None)

	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_run(job, run)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"

	remote_executor = worker_remote_instance._find_executor(run["identifier"])

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	remote_executor.succeed()

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "succeeded"

	# running => verifying
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "succeeded"

	await worker_local_instance.receive_update({ "run": run["identifier"], "event": "synchronization_completed" })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	# verifying => finishing
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "succeeded"

	# finishing => done (_finish_execution)
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1


@pytest.mark.asyncio
async def test_process_abort():
	""" Test executing a run which gets aborted """

	database_client_instance = MemoryDatabaseClient()
	data_storage_instance = MemoryDataStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	worker_storage_instance = Mock(spec = WorkerStorage)

	run_provider_instance = RunProvider(data_storage_instance, date_time_provider_instance)
	worker_remote_instance = FakeRemoteWorker(worker_storage_instance)
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance, None)

	job = { "project": "my_project", "identifier": "my_job" }
	run = run_provider_instance.create(database_client_instance, job["project"], job["identifier"], {}, None)

	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_run(job, run)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"

	remote_executor = worker_remote_instance._find_executor(run["identifier"])

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	worker_local_instance.abort_run(run["identifier"])

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	# running => aborting (_abort_execution)
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "aborting"
	assert run["status"] == "running"

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "aborting"
	assert run["status"] == "aborted"

	# aborting => verifying
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "aborted"

	await worker_local_instance.receive_update({ "run": run["identifier"], "event": "synchronization_completed" })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	# verifying => finishing
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "aborted"

	# finishing => done (_finish_execution)
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "aborted"
	assert len(worker_local_instance.executors) == 1


@pytest.mark.asyncio
async def test_process_recovery_during_execution(): # pylint: disable = too-many-statements
	""" Test executing a run which gets recovered after a disconnection and while it is running """

	database_client_instance = MemoryDatabaseClient()
	data_storage_instance = MemoryDataStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	worker_storage_instance = Mock(spec = WorkerStorage)

	run_provider_instance = RunProvider(data_storage_instance, date_time_provider_instance)
	worker_remote_instance = FakeRemoteWorker(worker_storage_instance)
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance, None)

	job = { "project": "my_project", "identifier": "my_job" }
	run = run_provider_instance.create(database_client_instance, job["project"], job["identifier"], {}, None)
	request = { "project_identifier": run["project"], "run_identifier": run["identifier"], "job_definition": job, "parameters": {} }

	worker_storage_instance.load_request.return_value = request

	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_run(job, run)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	remote_executor = worker_remote_instance._find_executor(run["identifier"])

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 1

	# New worker to simulate disconnection
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance, None)

	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 0

	# none => running (_recover_execution)
	worker_local_instance.executors = await worker_local_instance._recover_executors(database_client_instance)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 1

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	remote_executor.succeed()

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "succeeded"

	# running => verifying
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "succeeded"

	await worker_local_instance.receive_update({ "run": run["identifier"], "event": "synchronization_completed" })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	# verifying => finishing
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "succeeded"

	# finishing => done (_finish_execution)
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1


@pytest.mark.asyncio
async def test_process_recovery_after_execution(): # pylint: disable = too-many-statements
	""" Test executing a run which gets recovered after a disconnection and after it completed """

	database_client_instance = MemoryDatabaseClient()
	data_storage_instance = MemoryDataStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	worker_storage_instance = Mock(spec = WorkerStorage)

	run_provider_instance = RunProvider(data_storage_instance, date_time_provider_instance)
	worker_remote_instance = FakeRemoteWorker(worker_storage_instance)
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance, None)

	job = { "project": "my_project", "identifier": "my_job" }
	run = run_provider_instance.create(database_client_instance, job["project"], job["identifier"], {}, None)
	request = { "project_identifier": run["project"], "run_identifier": run["identifier"], "job_definition": job, "parameters": {} }

	worker_storage_instance.load_request.return_value = request

	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_run(job, run)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	remote_executor = worker_remote_instance._find_executor(run["identifier"])

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 1

	# New worker to simulate disconnection
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance, None)

	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 0

	remote_executor.succeed()

	# none => running (_recover_execution)
	worker_local_instance.executors = await worker_local_instance._recover_executors(database_client_instance)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "running"

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "succeeded"

	# running => verifying
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "succeeded"

	await worker_local_instance.receive_update({ "run": run["identifier"], "event": "synchronization_completed" })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	# verifying => finishing
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "succeeded"

	# finishing => done (_finish_execution)
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1

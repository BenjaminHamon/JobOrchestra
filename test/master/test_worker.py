 # pylint: disable = protected-access

""" Unit tests for Worker """

from unittest.mock import Mock, patch

import pytest

from bhamon_orchestra_model.database.memory_database_client import MemoryDatabaseClient
from bhamon_orchestra_model.database.memory_file_storage import MemoryFileStorage
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_master.worker import Worker as LocalWorker
from bhamon_orchestra_worker.worker import Worker as RemoteWorker

from ..fakes.executor_watcher import FakeExecutorWatcher

from ..fakes.fake_date_time_provider import FakeDateTimeProvider
from ..fakes.messenger import InProcessMessenger


RemoteWorker._resynchronize = lambda self, run_identifier, reset: None


@pytest.mark.asyncio
async def test_start_execution_success():
	""" Test _start_execution in normal conditions """

	run_provider_instance = Mock(spec = RunProvider)
	worker_remote_instance = RemoteWorker("my_worker", None, None, None, None, None, None)
	worker_remote_instance.executor_factory = FakeExecutorWatcher
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: None, run_provider_instance)

	job = { "identifier": "my_job" }
	run = { "identifier": "my_run", "job": job["identifier"], "status": "pending", "parameters": {} }

	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._start_execution(run, job)


@pytest.mark.asyncio
async def test_abort_execution_success():
	""" Test _abort_execution in normal conditions """

	run_provider_instance = Mock(spec = RunProvider)
	worker_remote_instance = RemoteWorker("my_worker", None, None, None, None, None, None)
	worker_remote_instance.executor_factory = FakeExecutorWatcher
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: None, run_provider_instance)

	job = { "identifier": "my_job" }
	run = { "identifier": "my_run", "job": job["identifier"], "status": "running", "steps": [] }

	worker_remote_instance._active_executors.append(FakeExecutorWatcher(run["identifier"]))

	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._abort_execution(run)


@pytest.mark.asyncio
async def test_finish_execution_success():
	""" Test _finish_execution in normal conditions """

	run_provider_instance = Mock(spec = RunProvider)
	worker_remote_instance = RemoteWorker("my_worker", None, None, None, None, None, None)
	worker_remote_instance.executor_factory = FakeExecutorWatcher
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: None, run_provider_instance)

	job = { "identifier": "my_job" }
	run = { "identifier": "my_run", "job": job["identifier"], "status": "succeeded", "steps": [] }

	worker_remote_instance._active_executors.append(FakeExecutorWatcher(run["identifier"]))

	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._finish_execution(run)


@pytest.mark.asyncio
async def test_process_success():
	""" Test executing a run which succeeds """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(file_storage_instance, date_time_provider_instance)
	worker_remote_instance = RemoteWorker("my_worker", None, None, None, None, None, None)
	worker_remote_instance.executor_factory = FakeExecutorWatcher
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance)

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
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"

	remote_executor = worker_remote_instance._find_executor(run["identifier"])

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	remote_executor.status["status"] = "succeeded"
	for step in remote_executor.status["steps"]:
		step["status"] = "succeeded"

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "succeeded"

	# running => verifying
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "succeeded"

	await worker_local_instance.receive_update({ "run": run["identifier"], "event": "synchronization_completed" })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	# verifying => finishing
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "succeeded"

	# finishing => done (_finish_execution)
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1


@pytest.mark.asyncio
async def test_process_abort(): # pylint: disable = too-many-statements
	""" Test executing a run which gets aborted """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(file_storage_instance, date_time_provider_instance)
	worker_remote_instance = RemoteWorker("my_worker", None, None, None, None, None, None)
	worker_remote_instance.executor_factory = FakeExecutorWatcher
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance)

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
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
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
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "aborting"
	assert run["status"] == "running"

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "aborting"
	assert run["status"] == "aborted"

	# aborting => verifying
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "aborted"

	await worker_local_instance.receive_update({ "run": run["identifier"], "event": "synchronization_completed" })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	# verifying => finishing
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "aborted"

	# finishing => done (_finish_execution)
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "aborted"
	assert len(worker_local_instance.executors) == 1


@pytest.mark.asyncio
async def test_process_recovery_during_execution(): # pylint: disable = too-many-statements
	""" Test executing a run which gets recovered after a disconnection and while it is running """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(file_storage_instance, date_time_provider_instance)
	worker_remote_instance = RemoteWorker("my_worker", None, None, None, None, None, None)
	worker_remote_instance.executor_factory = FakeExecutorWatcher
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance)

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
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	remote_executor = worker_remote_instance._find_executor(run["identifier"])
	remote_executor.request["job"] = job
	remote_executor.request["parameters"] = {}

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 1

	# New worker to simulate disconnection
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance)

	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 0

	# none => running (_recover_execution)
	with patch("bhamon_orchestra_worker.worker.worker_storage") as worker_storage_patch:
		worker_storage_patch.load_request = lambda run_identifier: remote_executor.request
		worker_local_instance.executors = await worker_local_instance._recover_executors(database_client_instance)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 1

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"

	remote_executor.status["status"] = "succeeded"
	for step in remote_executor.status["steps"]:
		step["status"] = "succeeded"

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "succeeded"

	# running => verifying
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "succeeded"

	await worker_local_instance.receive_update({ "run": run["identifier"], "event": "synchronization_completed" })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	# verifying => finishing
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "succeeded"

	# finishing => done (_finish_execution)
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1


@pytest.mark.asyncio
async def test_process_recovery_after_execution(): # pylint: disable = too-many-statements
	""" Test executing a run which gets recovered after a disconnection and after it completed """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	date_time_provider_instance = FakeDateTimeProvider()
	run_provider_instance = RunProvider(file_storage_instance, date_time_provider_instance)
	worker_remote_instance = RemoteWorker("my_worker", None, None, None, None, None, None)
	worker_remote_instance.executor_factory = FakeExecutorWatcher
	worker_messenger = InProcessMessenger(worker_remote_instance._handle_request)
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance)

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
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	remote_executor = worker_remote_instance._find_executor(run["identifier"])
	remote_executor.request["job"] = job
	remote_executor.request["parameters"] = {}

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 1

	# New worker to simulate disconnection
	worker_local_instance = LocalWorker("my_worker", worker_messenger, lambda: database_client_instance, run_provider_instance)

	assert run["status"] == "running"
	assert len(worker_local_instance.executors) == 0

	remote_executor.status["status"] = "succeeded"
	for step in remote_executor.status["steps"]:
		step["status"] = "succeeded"

	# none => running (_recover_execution)
	with patch("bhamon_orchestra_worker.worker.worker_storage") as worker_storage_patch:
		worker_storage_patch.load_request = lambda run_identifier: remote_executor.request
		worker_local_instance.executors = await worker_local_instance._recover_executors(database_client_instance)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "running"

	await worker_local_instance.receive_update({ "run": run["identifier"], "status": remote_executor.status })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "running"
	assert run["status"] == "succeeded"

	# running => verifying
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "verifying"
	assert run["status"] == "succeeded"

	await worker_local_instance.receive_update({ "run": run["identifier"], "event": "synchronization_completed" })
	await worker_local_instance._process_executor(database_client_instance, local_executor)

	# verifying => finishing
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "finishing"
	assert run["status"] == "succeeded"

	# finishing => done (_finish_execution)
	with patch("bhamon_orchestra_worker.worker.worker_storage"):
		await worker_local_instance._process_executor(database_client_instance, local_executor)

	assert local_executor["local_status"] == "done"
	assert run["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1

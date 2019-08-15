 # pylint: disable = protected-access

""" Unit tests for Worker """

import pytest

from bhamon_build_model.build_provider import BuildProvider
from bhamon_build_model.memory_database_client import MemoryDatabaseClient
from bhamon_build_model.memory_file_storage import MemoryFileStorage
from bhamon_build_master.worker import Worker

from .build_provider_fake import BuildProviderFake
from .worker_connection_mock import WorkerConnectionMock
from .worker_remote_mock import WorkerRemoteMock


@pytest.mark.asyncio
async def test_start_execution_success():
	""" Test _start_execution in normal conditions """

	build_provider_instance = BuildProviderFake()
	worker_remote_instance = WorkerRemoteMock("worker_test")
	worker_connection_instance = WorkerConnectionMock(worker_remote_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	job = { "identifier": "job_test" }
	build = { "identifier": "build_test", "job": job["identifier"], "status": "pending", "parameters": {} }
	await worker_local_instance._start_execution(build, job)


@pytest.mark.asyncio
async def test_abort_execution_success():
	""" Test _abort_execution in normal conditions """

	build_provider_instance = BuildProviderFake()
	worker_remote_instance = WorkerRemoteMock("worker_test")
	worker_connection_instance = WorkerConnectionMock(worker_remote_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	job = { "identifier": "job_test" }
	build = { "identifier": "build_test", "job": job["identifier"], "status": "running", "steps": [] }
	executor = { "job_identifier": job["identifier"], "build_identifier": build["identifier"] }
	executor["status"] = { "status": "running", "steps": [] }

	worker_remote_instance.executors.append(executor)
	await worker_local_instance._abort_execution(build)


@pytest.mark.asyncio
async def test_update_execution_success():
	""" Test _update_execution in normal conditions """

	build_provider_instance = BuildProviderFake()
	worker_remote_instance = WorkerRemoteMock("worker_test")
	worker_connection_instance = WorkerConnectionMock(worker_remote_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	job = { "identifier": "job_test" }
	build = { "identifier": "build_test", "job": job["identifier"], "status": "running", "steps": [] }
	executor = { "job_identifier": job["identifier"], "build_identifier": build["identifier"] }
	executor["status"] = { "status": "running", "steps": [] }

	worker_remote_instance.executors.append(executor)
	await worker_local_instance._update_execution(build)


@pytest.mark.asyncio
async def test_finish_execution_success():
	""" Test _finish_execution in normal conditions """

	build_provider_instance = BuildProviderFake()
	worker_remote_instance = WorkerRemoteMock("worker_test")
	worker_connection_instance = WorkerConnectionMock(worker_remote_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	job = { "identifier": "job_test" }
	build = { "identifier": "build_test", "job": job["identifier"], "status": "succeeded", "steps": [] }
	executor = { "job_identifier": job["identifier"], "build_identifier": build["identifier"] }
	executor["status"] = { "status": "succeeded", "steps": [] }

	worker_remote_instance.executors.append(executor)
	await worker_local_instance._finish_execution(build)


@pytest.mark.asyncio
async def test_process_success():
	""" Test running a build which succeeds """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	build_provider_instance = BuildProvider(database_client_instance, file_storage_instance)
	worker_remote_instance = WorkerRemoteMock("worker_test")
	worker_connection_instance = WorkerConnectionMock(worker_remote_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})

	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 0
	assert len(file_storage_instance.storage) == 0

	worker_local_instance.assign_build(job, build)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# running => running (_update_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert build["status"] == "running"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	remote_executor = worker_remote_instance.find_executor(build["identifier"])
	remote_executor["status"]["status"] = "succeeded"
	for step in remote_executor["status"]["steps"]:
		step["status"] = "succeeded"

	assert local_executor["local_status"] == "running"
	assert build["status"] == "running"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# running => done (_update_execution + _finish_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "done"
	assert build["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == len(remote_executor["status"]["steps"])


@pytest.mark.asyncio
async def test_process_abort():
	""" Test running a build which gets aborted """

	database_client_instance = MemoryDatabaseClient()
	file_storage_instance = MemoryFileStorage()
	build_provider_instance = BuildProvider(database_client_instance, file_storage_instance)
	worker_remote_instance = WorkerRemoteMock("worker_test")
	worker_connection_instance = WorkerConnectionMock(worker_remote_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})

	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 0
	assert len(file_storage_instance.storage) == 0

	worker_local_instance.assign_build(job, build)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# running => running (_update_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert build["status"] == "running"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	worker_local_instance.abort_build(build["identifier"])

	assert local_executor["local_status"] == "running"
	assert build["status"] == "running"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# running => aborting (_update_execution + _abort_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "aborting"
	assert build["status"] == "running"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# aborting => done (_update_execution + _finish_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "done"
	assert build["status"] == "aborted"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0


@pytest.mark.asyncio
async def test_process_recovery_during_execution(): # pylint: disable = too-many-statements
	""" Test running a build which gets recovered after a local exception and while it is running """

	database_client_instance = MemoryDatabaseClient()
	build_provider_instance = BuildProvider(database_client_instance, None)
	worker_remote_instance = WorkerRemoteMock("worker_test")
	worker_connection_instance = WorkerConnectionMock(worker_remote_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})

	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_build(job, build)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# running => exception (_update_execution)
	try:
		await worker_local_instance._process_executor(local_executor)
	except AttributeError:
		local_executor["local_status"] = "exception"
		build["status"] = "exception"

	assert local_executor["local_status"] == "exception"
	assert build["status"] == "exception"
	assert len(worker_local_instance.executors) == 1

	file_storage_instance = MemoryFileStorage()
	build_provider_instance = BuildProvider(database_client_instance, file_storage_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	assert build["status"] == "exception"
	assert len(worker_local_instance.executors) == 0

	# none => running (_recover_execution)
	worker_local_instance.executors = await worker_local_instance._recover_executors()
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "running"
	assert build["status"] == "exception"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# running => running (_update_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert build["status"] == "running"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	remote_executor = worker_remote_instance.find_executor(build["identifier"])
	remote_executor["status"]["status"] = "succeeded"
	for step in remote_executor["status"]["steps"]:
		step["status"] = "succeeded"

	assert local_executor["local_status"] == "running"
	assert build["status"] == "running"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# running => done (_update_execution + _finish_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "done"
	assert build["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == len(remote_executor["status"]["steps"])


@pytest.mark.asyncio
async def test_process_recovery_after_execution():
	""" Test running a build which gets recovered after a local exception and after it completed """

	database_client_instance = MemoryDatabaseClient()
	build_provider_instance = BuildProvider(database_client_instance, None)
	worker_remote_instance = WorkerRemoteMock("worker_test")
	worker_connection_instance = WorkerConnectionMock(worker_remote_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	job = { "identifier": "job_test" }
	build = build_provider_instance.create(job["identifier"], {})

	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 0

	worker_local_instance.assign_build(job, build)
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "pending"
	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# pending => running (_start_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "running"
	assert build["status"] == "pending"
	assert len(worker_local_instance.executors) == 1

	# running => exception (_update_execution)
	try:
		await worker_local_instance._process_executor(local_executor)
	except AttributeError:
		local_executor["local_status"] = "exception"
		build["status"] = "exception"

	assert local_executor["local_status"] == "exception"
	assert build["status"] == "exception"
	assert len(worker_local_instance.executors) == 1

	remote_executor = worker_remote_instance.find_executor(build["identifier"])
	remote_executor["status"]["status"] = "succeeded"
	for step in remote_executor["status"]["steps"]:
		step["status"] = "succeeded"

	assert local_executor["local_status"] == "exception"
	assert build["status"] == "exception"
	assert len(worker_local_instance.executors) == 1

	file_storage_instance = MemoryFileStorage()
	build_provider_instance = BuildProvider(database_client_instance, file_storage_instance)
	worker_local_instance = Worker("worker_test", worker_connection_instance, build_provider_instance)

	assert build["status"] == "exception"
	assert len(worker_local_instance.executors) == 0

	# none => running (_recover_execution)
	worker_local_instance.executors = await worker_local_instance._recover_executors()
	local_executor = worker_local_instance.executors[0]

	assert local_executor["local_status"] == "running"
	assert build["status"] == "exception"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == 0

	# running => done (_update_execution + _finish_execution)
	await worker_local_instance._process_executor(local_executor)

	assert local_executor["local_status"] == "done"
	assert build["status"] == "succeeded"
	assert len(worker_local_instance.executors) == 1
	assert len(file_storage_instance.storage) == len(remote_executor["status"]["steps"])

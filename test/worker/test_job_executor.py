""" Unit tests for JobExecutor """

import asyncio
import os
from unittest.mock import Mock, patch

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.serialization.serializer import Serializer
from bhamon_orchestra_worker.job_executor import JobExecutor
from bhamon_orchestra_worker.worker_storage import WorkerStorage

from ..mock_extensions import AsyncMock


async def test_empty(tmpdir):
	""" Test executing a job with no commands """

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)
	serializer_mock = Mock(spec = Serializer)

	executor_instance = JobExecutor(worker_storage_mock, date_time_provider_mock, serializer_mock)

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_pipeline",
		"run_identifier": "my_run",

		"job_definition": {
			"commands": [],
		},

		"parameters": {},
	}

	worker_storage_mock.get_log_path.return_value = log_file_path
	worker_storage_mock.load_request.return_value = request
	worker_storage_mock.load_results.return_value = {}

	executor_instance.run_identifier = request["run_identifier"]

	await executor_instance.initialize({})

	assert executor_instance.run_status == "pending"
	assert executor_instance.start_date is None
	assert executor_instance.completion_date is None

	with patch("bhamon_orchestra_worker.job_executor.ProcessWatcher"):
		await asyncio.wait_for(executor_instance.execute(), 1)

	assert executor_instance.run_status == "succeeded"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	await executor_instance.dispose()


async def test_simple(tmpdir):
	""" Test executing a job with a simple command """

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)
	serializer_mock = Mock(spec = Serializer)

	executor_instance = JobExecutor(worker_storage_mock, date_time_provider_mock, serializer_mock)

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_pipeline",
		"run_identifier": "my_run",

		"job_definition": {
			"commands": [
				[ "my_command" ],
			],
		},

		"parameters": {},
	}

	worker_storage_mock.get_log_path.return_value = log_file_path
	worker_storage_mock.load_request.return_value = request
	worker_storage_mock.load_results.return_value = {}

	executor_instance.run_identifier = request["run_identifier"]

	await executor_instance.initialize({})

	assert executor_instance.run_status == "pending"
	assert executor_instance.start_date is None
	assert executor_instance.completion_date is None

	with patch("bhamon_orchestra_worker.job_executor.ProcessWatcher") as process_watcher_class_mock:
		process_watcher_mock = process_watcher_class_mock.return_value
		process_watcher_mock.run = AsyncMock()
		process_watcher_mock.process.returncode = 0

		await asyncio.wait_for(executor_instance.execute(), 1)

	assert executor_instance.run_status == "succeeded"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	await executor_instance.dispose()

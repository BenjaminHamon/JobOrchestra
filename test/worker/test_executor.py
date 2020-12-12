""" Unit tests for Executor """

import os
from unittest.mock import Mock

import pytest

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.executor import Executor
from bhamon_orchestra_worker.worker_storage import WorkerStorage


@pytest.mark.asyncio
async def test_success(tmpdir):
	""" Test a run which succeeds """

	class DummyExecutor(Executor):
		async def execute_implementation(self):
			self.run_status = "succeeded"

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)

	executor_instance = DummyExecutor(worker_storage_mock, date_time_provider_mock)

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_job",
		"run_identifier": "my_run",
		"job_definition": {},
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

	await executor_instance.execute()

	assert executor_instance.run_status == "succeeded"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	await executor_instance.dispose()


@pytest.mark.asyncio
async def test_exception(tmpdir):
	""" Test a run which raises an exception """

	class DummyExecutor(Executor):
		async def execute_implementation(self):
			raise RuntimeError

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)

	executor_instance = DummyExecutor(worker_storage_mock, date_time_provider_mock)

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_job",
		"run_identifier": "my_run",
		"job_definition": {},
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

	await executor_instance.execute()

	assert executor_instance.run_status == "exception"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	await executor_instance.dispose()

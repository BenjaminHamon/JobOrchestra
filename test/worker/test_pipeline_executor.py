""" Unit tests for PipelineExecutor """

import asyncio
import os
from unittest.mock import Mock
import uuid

import pytest

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.pipeline_executor import PipelineExecutor
from bhamon_orchestra_worker.service_client import ServiceClient
from bhamon_orchestra_worker.worker_storage import WorkerStorage



class FakeServiceClient(ServiceClient):


	def __init__(self) -> None:
		self.all_runs = []


	def get_run(self, project_identifier: str, run_identifier: str) -> dict:
		for run in self.all_runs:
			if run["project"] == project_identifier and run["identifier"] == run_identifier:
				return run
		return None


	def trigger_job(self, project_identifier: str, job_identifier: str, parameters: dict, source: dict) -> dict:
		new_run = {
			"identifier": str(uuid.uuid4()),
			"project": project_identifier,
			"job": job_identifier,
			"parameters": parameters,
			"source": source,
			"status": "pending",
			"should_cancel": False,
			"should_abort": False,
		}

		self.all_runs.append(new_run)

		return { "run_identifier": new_run["identifier"] }


	def cancel_run(self, project_identifier: str, run_identifier: str) -> None:
		run = self.get_run(project_identifier, run_identifier)
		run["should_cancel"] = True


	def abort_run(self, project_identifier: str, run_identifier: str) -> None:
		run = self.get_run(project_identifier, run_identifier)
		run["should_abort"] = True



async def execute_runs(service_client: FakeServiceClient) -> None:
	while True:
		for run in service_client.all_runs:
			if run["status"] == "pending":
				if run["should_cancel"]:
					run["status"] = "cancelled"

			if run["status"] == "pending":
				if run["job"] == "success":
					run["status"] = "succeeded"
				if run["job"] == "failure":
					run["status"] = "failed"
				if run["job"] == "infinite":
					run["status"] = "running"

			if run["status"] == "running":
				if run["should_abort"]:
					run["status"] = "aborted"

		await asyncio.sleep(0.1)



@pytest.mark.asyncio
async def test_empty(tmpdir):
	""" Test executing a pipeline with no jobs """

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)
	service_client_mock = FakeServiceClient()

	executor_instance = PipelineExecutor(worker_storage_mock, date_time_provider_mock, service_client_mock)
	executor_instance.running_update_interval_seconds = 0.1
	executor_instance.aborting_update_interval_seconds = 0.1

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_pipeline",
		"run_identifier": "my_run",

		"job_definition": {
			"elements": [],
		},

		"parameters": {},
	}

	worker_storage_mock.get_log_path.return_value = log_file_path
	worker_storage_mock.load_request.return_value = request
	worker_storage_mock.load_results.return_value = {}

	service_future = asyncio.ensure_future(execute_runs(service_client_mock))

	executor_instance.run_identifier = request["run_identifier"]

	await executor_instance.initialize({})

	assert executor_instance.run_status == "pending"
	assert executor_instance.start_date is None
	assert executor_instance.completion_date is None

	await asyncio.wait_for(executor_instance.execute(), 1)

	assert executor_instance.run_status == "succeeded"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	assert len(executor_instance.all_inner_runs) == len(request["job_definition"]["elements"])
	for inner_run in executor_instance.all_inner_runs:
		assert inner_run["status"] == "succeeded"

	await executor_instance.dispose()

	service_future.cancel()


@pytest.mark.asyncio
async def test_parallel(tmpdir):
	""" Test executing a pipeline with parallel jobs """

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)
	service_client_mock = FakeServiceClient()

	executor_instance = PipelineExecutor(worker_storage_mock, date_time_provider_mock, service_client_mock)
	executor_instance.running_update_interval_seconds = 0.1
	executor_instance.aborting_update_interval_seconds = 0.1

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_pipeline",
		"run_identifier": "my_run",

		"job_definition": {
			"elements": [
				{ "identifier": "stage_1_job_1", "job": "success" },
				{ "identifier": "stage_1_job_2", "job": "success" },
				{ "identifier": "stage_1_job_3", "job": "success" },
			],
		},

		"parameters": {},
	}

	worker_storage_mock.get_log_path.return_value = log_file_path
	worker_storage_mock.load_request.return_value = request
	worker_storage_mock.load_results.return_value = {}

	service_future = asyncio.ensure_future(execute_runs(service_client_mock))

	executor_instance.run_identifier = request["run_identifier"]

	await executor_instance.initialize({})

	assert executor_instance.run_status == "pending"
	assert executor_instance.start_date is None
	assert executor_instance.completion_date is None

	await asyncio.wait_for(executor_instance.execute(), 1)

	assert executor_instance.run_status == "succeeded"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	assert len(executor_instance.all_inner_runs) == len(request["job_definition"]["elements"])
	for inner_run in executor_instance.all_inner_runs:
		assert inner_run["status"] == "succeeded"

	await executor_instance.dispose()

	service_future.cancel()


@pytest.mark.asyncio
async def test_sequential(tmpdir):
	""" Test executing a pipeline with sequential jobs """

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)
	service_client_mock = FakeServiceClient()

	executor_instance = PipelineExecutor(worker_storage_mock, date_time_provider_mock, service_client_mock)
	executor_instance.running_update_interval_seconds = 0.1
	executor_instance.aborting_update_interval_seconds = 0.1

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_pipeline",
		"run_identifier": "my_run",

		"job_definition": {
			"elements": [
				{ "identifier": "stage_1_job_1", "job": "success" },
				{ "identifier": "stage_2_job_1", "job": "success", "after": [ { "element": "stage_1_job_1", "status": [ "succeeded" ] } ] },
				{ "identifier": "stage_3_job_1", "job": "success", "after": [ { "element": "stage_2_job_1", "status": [ "succeeded" ] } ] },
			],
		},

		"parameters": {},
	}

	worker_storage_mock.get_log_path.return_value = log_file_path
	worker_storage_mock.load_request.return_value = request
	worker_storage_mock.load_results.return_value = {}

	service_future = asyncio.ensure_future(execute_runs(service_client_mock))

	executor_instance.run_identifier = request["run_identifier"]

	await executor_instance.initialize({})

	assert executor_instance.run_status == "pending"
	assert executor_instance.start_date is None
	assert executor_instance.completion_date is None

	await asyncio.wait_for(executor_instance.execute(), 1)

	assert executor_instance.run_status == "succeeded"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	assert len(executor_instance.all_inner_runs) == len(request["job_definition"]["elements"])
	for inner_run in executor_instance.all_inner_runs:
		assert inner_run["status"] == "succeeded"

	await executor_instance.dispose()

	service_future.cancel()


@pytest.mark.asyncio
async def test_complex(tmpdir):
	""" Test executing a pipeline with a complex set of jobs """

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)
	service_client_mock = FakeServiceClient()

	executor_instance = PipelineExecutor(worker_storage_mock, date_time_provider_mock, service_client_mock)
	executor_instance.running_update_interval_seconds = 0.1
	executor_instance.aborting_update_interval_seconds = 0.1

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_pipeline",
		"run_identifier": "my_run",

		"job_definition": {
			"elements": [
				{ "identifier": "stage_1_job_1", "job": "success" },
				{ "identifier": "stage_1_job_2", "job": "success" },
				{ "identifier": "stage_1_job_3", "job": "success" },

				{ "identifier": "stage_2_job_1", "job": "success", "after": [ { "element": "stage_1_job_1", "status": [ "succeeded" ] } ] },
				{ "identifier": "stage_2_job_2", "job": "success", "after": [ { "element": "stage_1_job_2", "status": [ "succeeded" ] } ] },
				{ "identifier": "stage_2_job_3", "job": "success", "after": [ { "element": "stage_1_job_3", "status": [ "succeeded" ] } ] },

				{ "identifier": "stage_3_job_1", "job": "success", "after": [ { "element": "stage_2_job_1", "status": [ "succeeded" ] } ] },
				{ "identifier": "stage_3_job_2", "job": "success", "after": [ { "element": "stage_2_job_2", "status": [ "succeeded" ] } ] },
				{ "identifier": "stage_3_job_3", "job": "success", "after": [ { "element": "stage_2_job_3", "status": [ "succeeded" ] } ] },
			],
		},

		"parameters": {},
	}

	worker_storage_mock.get_log_path.return_value = log_file_path
	worker_storage_mock.load_request.return_value = request
	worker_storage_mock.load_results.return_value = {}

	service_future = asyncio.ensure_future(execute_runs(service_client_mock))

	executor_instance.run_identifier = request["run_identifier"]

	await executor_instance.initialize({})

	assert executor_instance.run_status == "pending"
	assert executor_instance.start_date is None
	assert executor_instance.completion_date is None

	await asyncio.wait_for(executor_instance.execute(), 1)

	assert executor_instance.run_status == "succeeded"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	assert len(executor_instance.all_inner_runs) == len(request["job_definition"]["elements"])
	for inner_run in executor_instance.all_inner_runs:
		assert inner_run["status"] == "succeeded"

	await executor_instance.dispose()

	service_future.cancel()


@pytest.mark.asyncio
async def test_failure(tmpdir):
	""" Test executing a pipeline which fails """

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)
	service_client_mock = FakeServiceClient()

	executor_instance = PipelineExecutor(worker_storage_mock, date_time_provider_mock, service_client_mock)
	executor_instance.running_update_interval_seconds = 0.1
	executor_instance.aborting_update_interval_seconds = 0.1

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_pipeline",
		"run_identifier": "my_run",

		"job_definition": {
			"elements": [
				{ "identifier": "stage_1_job_1", "job": "success" },
				{ "identifier": "stage_2_job_1", "job": "failure", "after": [ { "element": "stage_1_job_1", "status": [ "succeeded" ] } ] },
				{ "identifier": "stage_3_job_1", "job": "success", "after": [ { "element": "stage_2_job_1", "status": [ "succeeded" ] } ] },
			],
		},

		"parameters": {},
	}

	worker_storage_mock.get_log_path.return_value = log_file_path
	worker_storage_mock.load_request.return_value = request
	worker_storage_mock.load_results.return_value = {}

	service_future = asyncio.ensure_future(execute_runs(service_client_mock))

	executor_instance.run_identifier = request["run_identifier"]

	await executor_instance.initialize({})

	assert executor_instance.run_status == "pending"
	assert executor_instance.start_date is None
	assert executor_instance.completion_date is None

	await asyncio.wait_for(executor_instance.execute(), 1)

	assert executor_instance.run_status == "failed"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	assert len(executor_instance.all_inner_runs) == len(request["job_definition"]["elements"])
	assert executor_instance.all_inner_runs[0]["status"] == "succeeded"
	assert executor_instance.all_inner_runs[1]["status"] == "failed"
	assert executor_instance.all_inner_runs[2]["status"] == "skipped"

	await executor_instance.dispose()

	service_future.cancel()


@pytest.mark.asyncio
async def test_abort(tmpdir):
	""" Test executing a pipeline which gets aborted """

	log_file_path = os.path.join(str(tmpdir), "run.log")

	worker_storage_mock = Mock(spec = WorkerStorage)
	date_time_provider_mock = Mock(spec = DateTimeProvider)
	service_client_mock = FakeServiceClient()

	executor_instance = PipelineExecutor(worker_storage_mock, date_time_provider_mock, service_client_mock)
	executor_instance.running_update_interval_seconds = 0.1
	executor_instance.aborting_update_interval_seconds = 0.1

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_pipeline",
		"run_identifier": "my_run",

		"job_definition": {
			"elements": [
				{ "identifier": "stage_1_job_1", "job": "infinite" },
				{ "identifier": "stage_2_job_1", "job": "success", "after": [ { "element": "stage_1_job_1", "status": [ "succeeded" ] } ] },
				{ "identifier": "stage_3_job_1", "job": "success", "after": [ { "element": "stage_2_job_1", "status": [ "succeeded" ] } ] },
			],
		},

		"parameters": {},
	}

	worker_storage_mock.get_log_path.return_value = log_file_path
	worker_storage_mock.load_request.return_value = request
	worker_storage_mock.load_results.return_value = {}

	service_future = asyncio.ensure_future(execute_runs(service_client_mock))

	executor_instance.run_identifier = request["run_identifier"]

	await executor_instance.initialize({})

	assert executor_instance.run_status == "pending"
	assert executor_instance.start_date is None
	assert executor_instance.completion_date is None

	execute_future = asyncio.ensure_future(executor_instance.execute())

	await asyncio.sleep(0.2)

	assert executor_instance.run_status == "running"
	assert executor_instance.all_inner_runs[0]["status"] == "running"

	execute_future.cancel()

	with pytest.raises(asyncio.CancelledError):
		await asyncio.wait_for(execute_future, 1)

	assert executor_instance.run_status == "aborted"
	assert executor_instance.start_date is not None
	assert executor_instance.completion_date is not None

	assert len(executor_instance.all_inner_runs) == len(request["job_definition"]["elements"])
	assert executor_instance.all_inner_runs[0]["status"] == "aborted"
	assert executor_instance.all_inner_runs[1]["status"] == "skipped"
	assert executor_instance.all_inner_runs[2]["status"] == "skipped"

	await executor_instance.dispose()

	service_future.cancel()

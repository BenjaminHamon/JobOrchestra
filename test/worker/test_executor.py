""" Unit tests for Executor """

import types

from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_worker.executor import Executor
from bhamon_orchestra_worker.worker_storage import WorkerStorage

from ..fakes.fake_date_time_provider import FakeDateTimeProvider


def test_success(tmpdir):
	""" Test a run which succeeds """

	def execute_implementation(self):
		self.run_status = "succeeded"

	data_storage_instance = FileDataStorage(str(tmpdir))
	worker_storage_instance = WorkerStorage(data_storage_instance)
	date_time_provider_instance = FakeDateTimeProvider()
	executor_instance = Executor(worker_storage_instance, date_time_provider_instance)

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_job",
		"run_identifier": "my_run",
		"job_definition": {},
		"parameters": {},
	}

	run_identifier = request["run_identifier"]

	worker_storage_instance.create_run(run_identifier)
	worker_storage_instance.save_request(run_identifier, request)

	executor_instance.run_identifier = run_identifier
	executor_instance.execute_implementation = types.MethodType(execute_implementation, executor_instance)

	status = worker_storage_instance.load_status(run_identifier)

	assert status is None

	executor_instance.initialize({})
	status = worker_storage_instance.load_status(run_identifier)

	assert status is not None
	assert status["project_identifier"] == request["project_identifier"]
	assert status["job_identifier"] == request["job_identifier"]
	assert status["run_identifier"] == request["run_identifier"]
	assert status["status"] == "pending"
	assert status["start_date"] is None
	assert status["completion_date"] is None

	executor_instance.execute()
	status = worker_storage_instance.load_status(run_identifier)

	assert status is not None
	assert status["project_identifier"] == request["project_identifier"]
	assert status["job_identifier"] == request["job_identifier"]
	assert status["run_identifier"] == request["run_identifier"]
	assert status["status"] == "succeeded"
	assert status["start_date"] is not None
	assert status["completion_date"] is not None


def test_exception(tmpdir):
	""" Test a run which raises an exception """

	def execute_implementation(self):
		raise RuntimeError

	data_storage_instance = FileDataStorage(str(tmpdir))
	worker_storage_instance = WorkerStorage(data_storage_instance)
	date_time_provider_instance = FakeDateTimeProvider()
	executor_instance = Executor(worker_storage_instance, date_time_provider_instance)

	request = {
		"project_identifier": "my_project",
		"job_identifier": "my_job",
		"run_identifier": "my_run",
		"job_definition": {},
		"parameters": {},
	}

	run_identifier = request["run_identifier"]

	worker_storage_instance.create_run(run_identifier)
	worker_storage_instance.save_request(run_identifier, request)

	executor_instance.run_identifier = run_identifier
	executor_instance.execute_implementation = types.MethodType(execute_implementation, executor_instance)

	status = worker_storage_instance.load_status(run_identifier)

	assert status is None

	executor_instance.initialize({})
	status = worker_storage_instance.load_status(run_identifier)

	assert status is not None
	assert status["project_identifier"] == request["project_identifier"]
	assert status["job_identifier"] == request["job_identifier"]
	assert status["run_identifier"] == request["run_identifier"]
	assert status["status"] == "pending"
	assert status["start_date"] is None
	assert status["completion_date"] is None

	executor_instance.execute()
	status = worker_storage_instance.load_status(run_identifier)

	assert status is not None
	assert status["project_identifier"] == request["project_identifier"]
	assert status["job_identifier"] == request["job_identifier"]
	assert status["run_identifier"] == request["run_identifier"]
	assert status["status"] == "exception"
	assert status["start_date"] is not None
	assert status["completion_date"] is not None

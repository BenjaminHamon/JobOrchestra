""" Unit tests for WorkerStorage """

from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_worker.worker_storage import WorkerStorage


def test_list_runs(tmpdir):
	""" Test listing runs """

	data_storage_instance = FileDataStorage(str(tmpdir))
	worker_storage_instance = WorkerStorage(data_storage_instance)

	uuid_run_identifier = "2152bd45-dd77-4cbb-998a-af21a52e4cea"
	arbitrary_run_identifier = "my_run"

	assert not worker_storage_instance.run_exists(uuid_run_identifier)
	assert not worker_storage_instance.run_exists(arbitrary_run_identifier)
	assert worker_storage_instance.list_runs() == []

	worker_storage_instance.create_run(uuid_run_identifier)
	worker_storage_instance.save_request(uuid_run_identifier, {})
	worker_storage_instance.create_run(arbitrary_run_identifier)
	worker_storage_instance.save_request(arbitrary_run_identifier, {})

	assert worker_storage_instance.run_exists(uuid_run_identifier)
	assert worker_storage_instance.run_exists(arbitrary_run_identifier)
	assert list(sorted(worker_storage_instance.list_runs())) == [ uuid_run_identifier, arbitrary_run_identifier ]

# pylint: disable = protected-access

""" Unit tests for Supervisor """

import pytest

from bhamon_orchestra_master.supervisor import RegistrationError, Supervisor
from bhamon_orchestra_model.database.memory_database_client import MemoryDatabaseClient
from bhamon_orchestra_model.worker_provider import WorkerProvider

from ..fakes.fake_date_time_provider import FakeDateTimeProvider


def test_register_worker_success():
	""" Test registering a worker successfully """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	worker_provider_instance = WorkerProvider(date_time_provider_instance)
	supervisor_instance = Supervisor(None, None, None, worker_provider_instance)

	worker_identifier = "my_worker"
	worker_version = "1.0"
	user_identifier = "my_user"

	worker_record = supervisor_instance._register_worker(database_client_instance, worker_identifier, worker_version, user_identifier)

	assert worker_record["identifier"] == worker_identifier
	assert worker_record["display_name"] == worker_identifier
	assert worker_record["version"] == worker_version
	assert worker_record["owner"] == user_identifier


def test_register_worker_already_active():
	""" Test registering a worker which is already active """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	worker_provider_instance = WorkerProvider(date_time_provider_instance)
	supervisor_instance = Supervisor(None, None, None, worker_provider_instance)

	worker_identifier = "my_worker"
	worker_version = "1.0"
	user_identifier = "my_user"

	supervisor_instance._active_workers[worker_identifier] = worker_identifier

	with pytest.raises(RegistrationError):
		supervisor_instance._register_worker(database_client_instance, worker_identifier, worker_version, user_identifier)


def test_register_worker_wrong_user():
	""" Test registering a worker which is already owned by another user """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	worker_provider_instance = WorkerProvider(date_time_provider_instance)
	supervisor_instance = Supervisor(None, None, None, worker_provider_instance)

	worker_identifier = "my_worker"
	worker_version = "1.0"
	user_identifier = "my_user"
	other_user_identifier = "other_user"

	worker_record = supervisor_instance._register_worker(database_client_instance, worker_identifier, worker_version, user_identifier)

	assert worker_record["owner"] == user_identifier

	with pytest.raises(RegistrationError):
		supervisor_instance._register_worker(database_client_instance, worker_identifier, worker_version, other_user_identifier)

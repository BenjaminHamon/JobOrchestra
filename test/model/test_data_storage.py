""" Unit tests for DataStorage """

import pytest

from bhamon_orchestra_model.database.data_storage import DataStorage
from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.database.memory_data_storage import MemoryDataStorage


def list_implementations():
	return [ "memory", "file" ]


def instantiate_implementation(temporary_directory, storage_implementation: str) -> DataStorage:
	if storage_implementation == "memory":
		return MemoryDataStorage()
	if storage_implementation == "file":
		return FileDataStorage(str(temporary_directory))

	raise ValueError("Unsupported implementation '%s'" % storage_implementation)


@pytest.mark.parametrize("storage_implementation", list_implementations())
def test_operations(tmpdir, storage_implementation):
	""" Test data storage operations """

	data_storage_instance = instantiate_implementation(tmpdir, storage_implementation)

	key = "my_key"
	data = "my_test_data".encode("utf-8")

	assert not data_storage_instance.exists(key)
	assert data_storage_instance.get_size(key) == 0
	assert data_storage_instance.get(key) is None
	assert data_storage_instance.get_chunk(key) is None

	data_storage_instance.set(key, data)

	assert data_storage_instance.exists(key)
	assert data_storage_instance.get_size(key) == len(data)
	assert data_storage_instance.get(key) == data
	assert data_storage_instance.get_chunk(key) == data
	assert data_storage_instance.get_chunk(key, skip = 2, limit = 5) == data[2:7]

	data_storage_instance.append(key, data)

	assert data_storage_instance.exists(key)
	assert data_storage_instance.get_size(key) == len(data) * 2
	assert data_storage_instance.get(key) == data * 2
	assert data_storage_instance.get_chunk(key) == data * 2
	assert data_storage_instance.get_chunk(key, skip = 2, limit = 5) == (data * 2)[2:7]

	data_storage_instance.delete(key)

	assert not data_storage_instance.exists(key)
	assert data_storage_instance.get_size(key) == 0
	assert data_storage_instance.get(key) is None
	assert data_storage_instance.get_chunk(key) is None

	data_storage_instance.delete(key)


@pytest.mark.parametrize("storage_implementation", list_implementations())
def test_get_keys(tmpdir, storage_implementation):
	""" Test listing keys """

	data_storage_instance = instantiate_implementation(tmpdir, storage_implementation)

	key = "my/key/with/slashes"
	data = "my_test_data".encode("utf-8")

	data_storage_instance.set(key, data)

	assert data_storage_instance.get_keys() == [ key ]

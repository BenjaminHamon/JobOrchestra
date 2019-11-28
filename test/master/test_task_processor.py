 # pylint: disable = protected-access

""" Unit tests for TaskProcessor """

from bhamon_build_model.task_provider import TaskProvider
from bhamon_build_model.database.memory_database_client import MemoryDatabaseClient
from bhamon_build_master.task_processor import TaskProcessor


def test_list_pending_tasks():
	""" Test listing pending tasks """

	database_client_instance = MemoryDatabaseClient()
	task_provider_instance = TaskProvider(database_client_instance)
	task_processor_instance = TaskProcessor(task_provider_instance)

	task_processor_instance.register_handler("test", 10, lambda parameters: "succeeded")

	first_test_task = task_provider_instance.create("test", {})
	unknown_task = task_provider_instance.create("unknown", {})
	second_test_task = task_provider_instance.create("test", {})

	task_collection = task_processor_instance._list_pending_tasks()

	assert task_collection == [ first_test_task, second_test_task, unknown_task ]


def test_execute_task_success():
	""" Test executing a task which succeeds """

	database_client_instance = MemoryDatabaseClient()
	task_provider_instance = TaskProvider(database_client_instance)
	task_processor_instance = TaskProcessor(task_provider_instance)

	task_processor_instance.register_handler("test", 10, lambda parameters: "succeeded")
	test_task = task_provider_instance.create("test", {})

	assert test_task["status"] == "pending"

	task_processor_instance._execute_task(test_task)

	assert test_task["status"] == "succeeded"


def test_execute_task_unknown():
	""" Test executing a task which has no handler """

	database_client_instance = MemoryDatabaseClient()
	task_provider_instance = TaskProvider(database_client_instance)
	task_processor_instance = TaskProcessor(task_provider_instance)

	unknown_task = task_provider_instance.create("unknown", {})

	assert unknown_task["status"] == "pending"

	try:
		task_processor_instance._execute_task(unknown_task)
	except KeyError:
		task_provider_instance.update_status(unknown_task, status = "exception")

	assert unknown_task["status"] == "exception"


def test_execute_task_cancellation():
	""" Test executing a task which was cancelled """

	database_client_instance = MemoryDatabaseClient()
	task_provider_instance = TaskProvider(database_client_instance)
	task_processor_instance = TaskProcessor(task_provider_instance)

	task_processor_instance.register_handler("test", 10, lambda parameters: "succeeded")
	test_task = task_provider_instance.create("test", {})
	task_provider_instance.update_status(test_task, should_cancel = True)

	assert test_task["status"] == "pending"
	assert test_task["should_cancel"]

	task_processor_instance._execute_task(test_task)

	assert test_task["status"] == "cancelled"


def test_execute_task_cancellation_handler():
	""" Test executing a task which was cancelled and has a cancellation handler """

	database_client_instance = MemoryDatabaseClient()
	task_provider_instance = TaskProvider(database_client_instance)
	task_processor_instance = TaskProcessor(task_provider_instance)

	task_processor_instance.register_handler("test", 10, lambda parameters: "succeeded", lambda parameters: None)
	test_task = task_provider_instance.create("test", {})
	task_provider_instance.update_status(test_task, should_cancel = True)

	assert test_task["status"] == "pending"
	assert test_task["should_cancel"]

	task_processor_instance._execute_task(test_task)

	assert test_task["status"] == "cancelled"

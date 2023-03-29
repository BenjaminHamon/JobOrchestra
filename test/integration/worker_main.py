import argparse
import logging
import sys
from typing import List

import filelock

import bhamon_orchestra_worker

from bhamon_orchestra_model.application import AsyncioApplication
from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer
from bhamon_orchestra_worker.master_client import MasterClient
from bhamon_orchestra_worker.worker import Worker
from bhamon_orchestra_worker.worker_storage import WorkerStorage

from . import environment


logger = logging.getLogger("Main")


def main():
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment.configure_logging(environment_instance, arguments)

	application_title = bhamon_orchestra_worker.__product__ + " " + "Worker"
	application_version = bhamon_orchestra_worker.__version__

	serializer_instance = JsonSerializer(indent = 4)
	authentication = serializer_instance.deserialize_from_file("authentication.json")

	with filelock.FileLock("worker.lock", 5):
		worker_application = create_application(arguments, authentication)
		asyncio_application = AsyncioApplication(application_title, application_version)
		asyncio_application.run_as_standalone(worker_application.run())


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--identifier", required = True, help = "Set the identifier for this worker")
	argument_parser.add_argument("--master-uri", required = True, help = "Set the websocket uri to the master")
	return argument_parser.parse_args()


def create_application(arguments, authentication):
	properties = {
		"project": [ "examples" ],
		"is_controller": arguments.identifier == "controller",
		"executor_limit": 100 if arguments.identifier == "controller" else 1,
	}

	data_storage_instance = FileDataStorage(".")
	serializer_instance = JsonSerializer(indent = 4)
	worker_storage_instance = WorkerStorage(data_storage_instance, serializer_instance)

	master_client_instance = MasterClient(
		master_uri = arguments.master_uri,
		worker_identifier = arguments.identifier,
		worker_version = bhamon_orchestra_worker.__version__,
		user = authentication["user"],
		secret = authentication["secret"],
	)

	def create_executor_command(run_request: dict) -> List[str]:
		return [ sys.executable, "-m", "test.integration.executor_main", run_request["run_identifier"] ]

	worker_instance = Worker(
		storage = worker_storage_instance,
		master_client = master_client_instance,
		display_name = arguments.identifier,
		properties = properties,
		executor_command_factory = create_executor_command,
	)

	return worker_instance


if __name__ == "__main__":
	main()

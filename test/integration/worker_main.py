import argparse
import json
import logging
import os

import filelock

from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_worker.worker import Worker
from bhamon_orchestra_worker.worker_storage import WorkerStorage

import environment


logger = logging.getLogger("Worker")


def main():
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment.configure_logging(environment_instance, arguments)

	executor_script = os.path.join(os.path.dirname(__file__), "executor_main.py")

	authentication_file_path = os.path.join(os.getcwd(), "authentication.json")
	with open(authentication_file_path, mode = "r", encoding = "utf-8") as authentication_file:
		authentication = json.load(authentication_file)

	with filelock.FileLock("worker.lock", 5):
		worker_instance = create_application(arguments, authentication, executor_script)
		worker_instance.run()


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--identifier", required = True, help = "Set the identifier for this worker")
	argument_parser.add_argument("--master-uri", required = True, help = "Set the websocket uri to the master")
	return argument_parser.parse_args()


def create_application(arguments, authentication, executor_script):
	properties = {
		"project": [ "examples" ],
		"is_controller": arguments.identifier == "controller",
		"executor_limit": 100 if arguments.identifier == "controller" else 1,
	}

	data_storage_instance = FileDataStorage(".")
	worker_storage_instance = WorkerStorage(data_storage_instance)

	worker_instance = Worker(
		storage = worker_storage_instance,
		identifier = arguments.identifier,
		master_uri = arguments.master_uri,
		user = authentication["user"],
		secret = authentication["secret"],
		display_name = arguments.identifier,
		properties = properties,
		executor_script = executor_script,
	)

	return worker_instance


if __name__ == "__main__":
	main()

import argparse
import logging
import os

import filelock

from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.executor import Executor
from bhamon_orchestra_worker.worker_storage import WorkerStorage

import environment


logger = logging.getLogger("Executor")


def main():
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment_instance["script_root"] = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
	environment_instance["orchestra_worker_authentication"] = os.path.join(os.getcwd(), "authentication.json")
	environment.configure_logging(environment_instance, arguments)

	with filelock.FileLock(os.path.join("runs", arguments.run_identifier, "executor.lock"), 5):
		executor_instance = create_application(arguments)
		executor_instance.run(environment_instance)


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("run_identifier", help = "Set the run identifier")
	return argument_parser.parse_args()


def create_application(arguments):
	data_storage_instance = FileDataStorage(".")
	date_time_provider_instance = DateTimeProvider()
	worker_storage_instance = WorkerStorage(data_storage_instance)

	executor_instance = Executor(
		storage = worker_storage_instance,
		date_time_provider = date_time_provider_instance,
		run_identifier = arguments.run_identifier,
	)

	return executor_instance


if __name__ == "__main__":
	main()

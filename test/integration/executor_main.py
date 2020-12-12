import argparse
import logging
import os

import filelock

import bhamon_orchestra_worker

from bhamon_orchestra_model.application import AsyncioApplication
from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.job_executor import JobExecutor
from bhamon_orchestra_worker.worker_storage import WorkerStorage

import environment


logger = logging.getLogger("Main")


def main():
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment_instance["script_root"] = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
	environment_instance["orchestra_worker_authentication"] = os.path.join(os.getcwd(), "authentication.json")
	environment.configure_logging(environment_instance, arguments)

	application_title = bhamon_orchestra_worker.__product__ + " " + "Executor"
	application_version = bhamon_orchestra_worker.__version__

	with filelock.FileLock(os.path.join("runs", arguments.run_identifier, "executor.lock"), 5):
		executor_application = create_application()
		asyncio_application = AsyncioApplication(application_title, application_version)
		asyncio_application.run_as_standalone(executor_application.run(arguments.run_identifier, environment_instance))


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("run_identifier", help = "Set the run identifier")
	return argument_parser.parse_args()


def create_application():
	data_storage_instance = FileDataStorage(".")
	date_time_provider_instance = DateTimeProvider()
	worker_storage_instance = WorkerStorage(data_storage_instance)

	executor_instance = JobExecutor(
		storage = worker_storage_instance,
		date_time_provider = date_time_provider_instance,
	)

	return executor_instance


if __name__ == "__main__":
	main()

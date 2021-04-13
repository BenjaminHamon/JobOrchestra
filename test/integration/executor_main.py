import argparse
import logging
import os

import filelock

import bhamon_orchestra_worker

from bhamon_orchestra_model.application import AsyncioApplication
from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer
from bhamon_orchestra_worker.job_executor import JobExecutor
from bhamon_orchestra_worker.pipeline_executor import PipelineExecutor
from bhamon_orchestra_worker.web_service_client import WebServiceClient
from bhamon_orchestra_worker.worker_storage import WorkerStorage

from . import environment


logger = logging.getLogger("Main")


def main():
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment_instance["orchestra_worker_authentication"] = os.path.join(os.getcwd(), "authentication.json")
	environment.configure_logging(environment_instance, arguments)

	application_title = bhamon_orchestra_worker.__product__ + " " + "Executor"
	application_version = bhamon_orchestra_worker.__version__

	configuration = {
		"orchestra_service_url": environment_instance["orchestra_service_url"],
	}

	serializer_instance = JsonSerializer(indent = 4)
	authentication = serializer_instance.deserialize_from_file("authentication.json")

	with filelock.FileLock(os.path.join("runs", arguments.run_identifier, "executor.lock"), 5):
		executor_application = create_application(arguments.run_identifier, configuration, authentication)
		asyncio_application = AsyncioApplication(application_title, application_version)
		asyncio_application.run_as_standalone(executor_application.run(arguments.run_identifier, environment_instance))


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("run_identifier", help = "Set the run identifier")
	return argument_parser.parse_args()


def create_application(run_identifier, configuration, authentication):
	service_authorization = (authentication["user"], authentication["secret"])

	data_storage_instance = FileDataStorage(".")
	date_time_provider_instance = DateTimeProvider()
	serializer_instance = JsonSerializer(indent = 4)
	worker_storage_instance = WorkerStorage(data_storage_instance, serializer_instance)
	service_client_instance = WebServiceClient(serializer_instance, configuration["orchestra_service_url"], authorization = service_authorization)

	request = worker_storage_instance.load_request(run_identifier)

	if request["job_definition"]["type"] == "job":
		executor_instance = JobExecutor(
			storage = worker_storage_instance,
			date_time_provider = date_time_provider_instance,
			serializer = serializer_instance,
		)

	elif request["job_definition"]["type"] == "pipeline":
		executor_instance = PipelineExecutor(
			storage = worker_storage_instance,
			date_time_provider = date_time_provider_instance,
			serializer = serializer_instance,
			service_client = service_client_instance,
		)

		# Rapid updates to reduce delays in tests
		executor_instance.running_update_interval_seconds = 1
		executor_instance.aborting_update_interval_seconds = 1

	else:
		raise RuntimeError("Unsupported job definition")

	return executor_instance


if __name__ == "__main__":
	main()

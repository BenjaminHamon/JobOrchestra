import argparse
import logging
import os

import filelock

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.executor import Executor

import environment


def main():
	arguments = parse_arguments()
	environment.configure_logging(logging.INFO)
	environment_instance = environment.load_environment()
	environment_instance["script_root"] = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
	environment_instance["orchestra_worker_authentication"] = os.path.join(os.getcwd(), "authentication.json")
	executor_run_directory = os.path.join("runs", arguments.job_identifier + "_" + arguments.run_identifier)

	with filelock.FileLock(os.path.join(executor_run_directory, "executor.lock"), 5):
		executor_instance = create_application(arguments)
		executor_instance.run(environment_instance)


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("job_identifier", help = "Set the job identifier")
	argument_parser.add_argument("run_identifier", help = "Set the run identifier")
	return argument_parser.parse_args()


def create_application(arguments):
	date_time_provider_instance = DateTimeProvider()

	executor_instance = Executor(
		job_identifier = arguments.job_identifier,
		run_identifier = arguments.run_identifier,
		date_time_provider = date_time_provider_instance,
	)

	return executor_instance


if __name__ == "__main__":
	main()

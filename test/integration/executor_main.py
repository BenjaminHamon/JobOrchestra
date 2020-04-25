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

	with filelock.FileLock(os.path.join("runs", arguments.run_identifier, "executor.lock"), 5):
		executor_instance = create_application(arguments)
		executor_instance.run(environment_instance)


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("run_identifier", help = "Set the run identifier")
	return argument_parser.parse_args()


def create_application(arguments):
	date_time_provider_instance = DateTimeProvider()

	executor_instance = Executor(
		run_identifier = arguments.run_identifier,
		date_time_provider = date_time_provider_instance,
	)

	return executor_instance


if __name__ == "__main__":
	main()

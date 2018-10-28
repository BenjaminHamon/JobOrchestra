import argparse
import logging
import os

import filelock

import bhamon_build_worker.executor as executor

import environment


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("job_identifier", help = "Set the job identifier")
	argument_parser.add_argument("build_identifier", help = "Set the build identifier")
	return argument_parser.parse_args()


if __name__ == "__main__":
	arguments = parse_arguments()
	environment.configure_logging(logging.INFO)
	environment_instance = environment.load_environment()
	executor_build_directory = os.path.join("builds", arguments.job_identifier + "_" + arguments.build_identifier)

	with filelock.FileLock(os.path.join(executor_build_directory, "build_executor.lock"), 5):
		executor.run(arguments.job_identifier, arguments.build_identifier, environment_instance)

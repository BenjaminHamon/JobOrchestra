import argparse
import logging
import os

import filelock

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
		executor_instance = Executor(arguments.job_identifier, arguments.run_identifier)
		executor_instance.run(environment_instance)


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("job_identifier", help = "Set the job identifier")
	argument_parser.add_argument("run_identifier", help = "Set the run identifier")
	return argument_parser.parse_args()


if __name__ == "__main__":
	main()

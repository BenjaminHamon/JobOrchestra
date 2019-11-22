import argparse
import json
import logging
import os

import filelock

from bhamon_build_worker.worker import Worker

import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()
	executor_script = os.path.join(os.path.dirname(__file__), "executor_main.py")

	authentication_file_path = os.path.join(os.getcwd(), "authentication.json")
	with open(authentication_file_path, "r") as authentication_file:
		authentication = json.load(authentication_file)

	with filelock.FileLock("build_worker.lock", 5):
		worker_instance = Worker(arguments.identifier, arguments.master_uri, authentication["user"], authentication["secret"], executor_script)
		worker_instance.run()


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--identifier", required = True, help = "Set the identifier for this worker")
	argument_parser.add_argument("--master-uri", required = True, help = "Set the websocket uri to the build master")
	return argument_parser.parse_args()


if __name__ == "__main__":
	main()

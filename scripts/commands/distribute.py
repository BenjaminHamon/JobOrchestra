import argparse
import logging
import os
import shutil
import subprocess


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	command_list = [ "package", "upload" ]

	parser = subparsers.add_parser("distribute", formatter_class = argparse.RawTextHelpFormatter, help = "create distribution packages")
	parser.add_argument("--command", choices = command_list, nargs = "+", dest = "distribute_commands",
		metavar = "<command>", help = "set the command(s) to execute for distribution" + "\n" + "(%s)" % ", ".join(command_list))
	parser.add_argument("--force", action = "store_true", help = "if a distribution was already uploaded, overwrite it")
	return parser


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	if not arguments.distribute_commands:
		raise ValueError("No command was selected")

	if "package" in arguments.distribute_commands:
		for component in configuration["components"]:
			create(environment["python3_executable"], component, arguments.verbosity == "debug", arguments.simulate)
	if "upload" in arguments.distribute_commands:
		for component in configuration["components"]:
			upload(environment["python_package_repository"], component, configuration["project_version"], arguments.force, arguments.simulate)
			logging.info("")


def create(python_executable, component, verbose, simulate):
	logging.info("Creating distribution for '%s'", component["name"])

	output_directory = os.path.join("..", ".build", component["path"])

	setup_command = [ python_executable, "setup.py" ]
	setup_command += [ "--quiet" ] if not verbose else []
	setup_command += [ "--dry-run" ] if simulate else []
	setup_command += [ "sdist", "--dist-dir", output_directory, "--format", "zip" ]

	logging.info("+ %s", " ".join(setup_command))
	subprocess.check_call(setup_command, cwd = component["path"])


def upload(package_repository, component, version, force, simulate):
	logging.info("Uploading distribution for '%s'", component["name"])

	archive_name = component["name"] + "-" + version["full"] + ".zip"
	source_path = os.path.join(".build", component["path"], archive_name)
	destination_path = os.path.join(package_repository, component["name"], archive_name) 

	logging.info("Uploading '%s' to '%s'", source_path, destination_path)

	if os.path.isfile(destination_path):
		if not force:
			raise ValueError("Destination already exists: '%s'" % destination_path)
		if not simulate:
			os.remove(destination_path)

	if not simulate:
		os.makedirs(os.path.dirname(destination_path), exist_ok = True)
		shutil.copyfile(source_path, destination_path + ".tmp")
		shutil.move(destination_path + ".tmp", destination_path)

import argparse
import logging
import os
import shutil
import subprocess

import bhamon_development_toolkit.python.distribution
import bhamon_development_toolkit.workspace


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	available_commands = [ "setup", "package", "upload" ]

	def parse_command_parameter(argument_value):
		command_list = argument_value.split("+")
		for command in command_list:
			if command not in available_commands:
				raise argparse.ArgumentTypeError("invalid distribute command: '%s'" % command)
		return command_list

	parser = subparsers.add_parser("distribute", help = "create distribution packages")
	parser.add_argument("distribute_commands", type = parse_command_parameter,
		metavar = "<command[+command]>", help = "set the command(s) to execute for the distribution, separated by '+' (%s)" % ", ".join(available_commands))
	return parser


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	repository_client = None
	if environment.get("python_package_repository_url", None) is not None:
		repository_url = environment["python_package_repository_url"]
		repository_parameters = environment.get("python_package_repository_parameters", {})
		repository_client = bhamon_development_toolkit.python.distribution.create_repository_client(repository_url, repository_parameters, environment)

	if "upload" in arguments.distribute_commands and repository_client is None:
		raise ValueError("Upload command requires a python package repository")

	if "setup" in arguments.distribute_commands:
		for component in configuration["components"]:
			setup(configuration, component, arguments.simulate)
		print("")
	if "package" in arguments.distribute_commands:
		for component in configuration["components"]:
			package(environment["python3_executable"], component, configuration["project_version"], arguments.verbosity == "debug", arguments.simulate)
			print("")
	if "upload" in arguments.distribute_commands:
		for component in configuration["components"]:
			repository_client.upload(os.path.join(".artifacts", "distributions"), component["name"], configuration["project_version"], "-py3-none-any.whl", arguments.simulate)
			save_upload_results(component, configuration["project_version"], arguments.results, arguments.simulate)
			print("")


def setup(configuration, component, simulate):
	logger.info("Generating metadata for '%s'", component["name"])

	metadata_file_path = os.path.join(component["path"], component["packages"][0], "__metadata__.py")
	metadata_content = ""
	metadata_content += "__copyright__ = \"%s\"\n" % configuration["copyright"]
	metadata_content += "__version__ = \"%s\"\n" % configuration["project_version"]["full"]
	metadata_content += "__date__ = \"%s\"\n" % configuration["project_version"]["date"]

	if not simulate:
		with open(metadata_file_path, "w", encoding = "utf-8") as metadata_file:
			metadata_file.writelines(metadata_content)


def package(python_executable, component, version, verbose, simulate):
	logger.info("Creating distribution for '%s'", component["name"])

	if os.sep in os.path.normpath(python_executable):
		python_executable = os.path.abspath(python_executable)

	setup_command = [ python_executable, "setup.py" ]
	setup_command += [ "--quiet" ] if not verbose else []
	setup_command += [ "bdist_wheel" ]

	logger.info("+ %s", " ".join(setup_command))
	if not simulate:
		subprocess.check_call(setup_command, cwd = component["path"])

	archive_name = component["name"].replace("-", "_") + "-" + version["full"]
	source_path = os.path.join(component["path"], "dist", archive_name + "-py3-none-any.whl")
	destination_path = os.path.join(".artifacts", "distributions", component["name"], archive_name + "-py3-none-any.whl")

	if not simulate:
		os.makedirs(os.path.dirname(destination_path), exist_ok = True)
		shutil.copyfile(source_path, destination_path + ".tmp")
		shutil.move(destination_path + ".tmp", destination_path)


def save_upload_results(component, version, result_file_path, simulate):
	distribution_information = {
		"name": component["name"],
		"version": version["full"],
	}

	if result_file_path:
		results = bhamon_development_toolkit.workspace.load_results(result_file_path)
		results["distributions"] = results.get("distributions", [])
		results["distributions"].append(distribution_information)
		if not simulate:
			bhamon_development_toolkit.workspace.save_results(result_file_path, results)

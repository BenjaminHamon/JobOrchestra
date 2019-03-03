import argparse
import glob
import json
import logging
import os
import shutil
import subprocess


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	command_list = [ "setup", "package", "upload" ]

	parser = subparsers.add_parser("distribute", formatter_class = argparse.RawTextHelpFormatter, help = "create distribution packages")
	parser.add_argument("--command", required = True, choices = command_list, nargs = "+", dest = "distribute_commands",
		metavar = "<command>", help = "set the command(s) to execute for distribution" + "\n" + "(%s)" % ", ".join(command_list))
	return parser


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	if "setup" in arguments.distribute_commands:
		for component in configuration["components"]:
			setup(configuration, component, arguments.simulate)
		print("")
	if "package" in arguments.distribute_commands:
		for component in configuration["components"]:
			create(environment["python3_executable"], component, arguments.verbosity == "debug", arguments.simulate)
			print("")
	if "upload" in arguments.distribute_commands:
		package_repository = os.path.normpath(environment["python_package_repository"])
		for component in configuration["components"]:
			upload(package_repository, component, configuration["project_version"], arguments.simulate, arguments.results)
			print("")


# Setup scripts are generated from a template to avoid having a dependency on scripts which are not packaged.
def setup(configuration, component, simulate):
	logging.info("Generating setup.py script for '%s'", component["name"])

	template_file_path = os.path.join(component["path"], "setup.template.py")
	output_path = os.path.join(component["path"], "setup.py")

	with open(template_file_path, "r") as template_file:
		script_content = template_file.read()
	script_content = script_content.replace("{version}", configuration["project_version"]["full"])
	script_content = script_content.replace("{author}", configuration["author"])
	script_content = script_content.replace("{author_email}", configuration["author_email"])
	script_content = script_content.replace("{url}", configuration["project_url"])

	if not simulate:
		with open(output_path, "w") as output_file:
			output_file.write(script_content)


def create(python_executable, component, verbose, simulate):
	logging.info("Creating distribution for '%s'", component["name"])

	output_directory = os.path.join("..", ".build", component["path"])

	setup_command = [ python_executable, "setup.py" ]
	setup_command += [ "--quiet" ] if not verbose else []
	setup_command += [ "--dry-run" ] if simulate else []
	setup_command += [ "sdist", "--dist-dir", output_directory, "--format", "zip" ]

	logging.info("+ %s", " ".join(setup_command))
	subprocess.check_call(setup_command, cwd = component["path"])


def upload(package_repository, component, version, simulate, result_file_path):
	logging.info("Uploading distribution for '%s'", component["name"])

	archive_name = component["name"] + "-" + version["full"]
	source_path = os.path.join(".build", component["path"], archive_name + ".zip")
	destination_path = os.path.join(package_repository, component["name"], archive_name + ".zip")

	existing_distribution_pattern = component["name"] + "-" + version["identifier"] + "+*.zip"
	existing_distribution = next((x for x in glob.glob(os.path.join(package_repository, component["name"], existing_distribution_pattern))), None)
	if existing_distribution is not None:
		raise ValueError("Version %s already exists: '%s'" % (version["identifier"], os.path.basename(existing_distribution)))

	logging.info("Uploading '%s' to '%s'", source_path, destination_path)

	if not simulate:
		os.makedirs(os.path.dirname(destination_path), exist_ok = True)
		shutil.copyfile(source_path, destination_path + ".tmp")
		shutil.move(destination_path + ".tmp", destination_path)

	if result_file_path:
		results = _load_results(result_file_path)
		results["artifacts"].append({ "name": archive_name, "path": destination_path })
		if not simulate:
			_save_results(result_file_path, results)


def _load_results(result_file_path):
	if not os.path.isfile(result_file_path):
		return { "artifacts": [] }
	with open(result_file_path, "r") as result_file:
		results = json.load(result_file)
		results["artifacts"] = results.get("artifacts", [])
	return results


def _save_results(result_file_path, result_data):
	if os.path.dirname(result_file_path):
		os.makedirs(os.path.dirname(result_file_path), exist_ok = True)
	with open(result_file_path, "w") as result_file:
		json.dump(result_data, result_file, indent = 4)

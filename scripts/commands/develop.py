import logging
import os
import subprocess

import scripts.commands.distribute


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("develop", help = "setup workspace for development")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	for component in configuration["components"]:
		scripts.commands.distribute.setup(configuration, component, arguments.simulate)
	print("")
	install(environment["python3_executable"], configuration["development_dependencies"], configuration["components"], arguments.simulate)
	print("")


def install(python_executable, dependency_collection, component_collection, simulate):
	logger.info("Installing development dependencies")

	install_command = [ python_executable, "-m", "pip", "install", "--upgrade" ] + dependency_collection
	logger.info("+ %s", " ".join(install_command))
	if not simulate:
		subprocess.check_call(install_command)
		print("")

	for component in component_collection:
		logger.info("Installing development package for '%s'", component["name"])

		install_command = [ python_executable, "-m", "pip", "install", "--upgrade", "--editable", os.path.join(".", component["path"]) ]
		logger.info("+ %s", " ".join(install_command))
		if not simulate:
			subprocess.check_call(install_command)
			print("")

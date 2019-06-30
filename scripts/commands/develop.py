import logging
import os
import subprocess

import scripts.commands.distribute


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("develop", help = "setup workspace for development")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	install_dependencies(environment["python3_executable"], configuration["development_dependencies"], arguments.simulate)
	print("")
	for component in configuration["components"]:
		scripts.commands.distribute.setup(configuration, component, arguments.simulate)
	print("")
	for component in configuration["components"]:
		install_component(environment["python3_executable"], component, arguments.simulate)
		print("")


def install_dependencies(python_executable, dependency_collection, simulate):
	logger.info("Installing development dependencies")

	install_command = [ python_executable, "-m", "pip", "install", "--upgrade" ] + dependency_collection
	logger.info("+ %s", " ".join(install_command))
	if not simulate:
		subprocess.check_call(install_command)


def install_component(python_executable, component, simulate):
	logger.info("Installing development package for '%s'", component["name"])

	install_command = [ python_executable, "-m", "pip", "install", "--upgrade", "--editable", os.path.join(".", component["path"]) ]
	logger.info("+ %s", " ".join(install_command))
	if not simulate:
		subprocess.check_call(install_command)

import logging
import os
import subprocess

import commands.distribute


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("develop", help = "setup workspace for development")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	for component in configuration["components"]:
		commands.distribute.setup(configuration, component, arguments.simulate)
	print("")
	install(environment["python3_executable"], configuration["components"], arguments.simulate)
	print("")


def install(python_executable, component_collection, simulate):
	logging.info("Installing development dependencies")

	install_command = [ python_executable, "-m", "pip", "install", "--upgrade", "pylint", "pytest", "wheel" ]
	logging.info("+ %s", " ".join(install_command))
	if not simulate:
		subprocess.check_call(install_command)
		print("")

	logging.info("Installing development packages")

	install_command = [ python_executable, "-m", "pip", "install", "--upgrade", "--editable" ]
	install_command += [ os.path.join(".", component["path"]) for component in component_collection ]
	logging.info("+ %s", " ".join(install_command))
	if not simulate:
		subprocess.check_call(install_command)
		print("")

import logging
import subprocess

import commands.distribute


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("develop", help = "setup workspace for development")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	for component in configuration["components"]:
		commands.distribute.setup(configuration, component, arguments.simulate)
	print("")
	for component in configuration["components"]:
		install(environment["python3_executable"], component, arguments.simulate)
		print("")


def install(python_executable, component, simulate):
	logging.info("Installing '%s'", component["name"])

	install_command = [ python_executable, "-m", "pip", "install", "--editable", component["path"] ]
	logging.info("+ %s", " ".join(install_command))
	if not simulate:
		subprocess.check_call(install_command)

import logging
import os
import shutil
import sys

sys.path.insert(0, os.path.join(sys.path[0], ".."))

import development.configuration # pylint: disable = wrong-import-position
import development.environment # pylint: disable = wrong-import-position


logger = logging.getLogger("Main")


def main():
	with development.environment.execute_in_workspace(__file__):
		environment_instance = development.environment.load_environment()
		configuration_instance = development.configuration.load_configuration(environment_instance)
		development.environment.configure_logging(environment_instance, None)

		global_status = { "success": True }

		check_commands(global_status)
		check_software(global_status, environment_instance)

	if not global_status["success"]:
		raise RuntimeError("Check found issues")


def check_commands(global_status):
	command_list = development.configuration.load_commands()

	for command in command_list:
		if "exception" in command:
			global_status["success"] = False
			logger.error("Command '%s' is unavailable", command["module_name"], exc_info = command["exception"])
			print("")


def check_software(global_status, environment_instance):
	python3_system_executable = environment_instance.get("python3_system_executable", None)
	if python3_system_executable is None or not shutil.which(python3_system_executable):
		global_status["success"] = False
		logger.error("Python3 is required (Path: '%s')", environment_instance["python3_system_executable"])


if __name__ == "__main__":
	main()

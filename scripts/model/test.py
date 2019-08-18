import logging
import os
import subprocess


logger = logging.getLogger("Test")


def run_pytest(python_executable, output_directory, run_identifier, target, filter_expression, simulate):
	pytest_command = [ python_executable, "-m", "pytest", target, "--verbose" ]
	pytest_command += [ "--collect-only" ] if simulate else []
	pytest_command += [ "--basetemp", os.path.join(output_directory, str(run_identifier)) ]
	pytest_command += [ "--json", os.path.join(output_directory, str(run_identifier) + ".json") ]
	pytest_command += [ "-k", filter_expression ] if filter_expression else []

	if not simulate:
		os.makedirs(output_directory, exist_ok = True)

	logger.info("+ %s", " ".join(pytest_command))
	subprocess.check_call(pytest_command)

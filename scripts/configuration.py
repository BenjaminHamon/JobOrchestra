import subprocess

import commands.clean
import commands.lint
import commands.test


def get_command_list():
	return [
		commands.clean,
		commands.lint,
		commands.test,
	]


def load_configuration(environment):
	configuration = {
		"project": "bhamon-build",
		"project_name": "Build Service",
		"project_version": { "identifier": "1.0" },
	}

	configuration["packages"] = [
		"master/bhamon_build_master",
		"model/bhamon_build_model",
		"service/bhamon_build_service",
		"website/bhamon_build_website",
		"worker/bhamon_build_worker",
	]

	configuration["project_version"]["revision"] = subprocess.check_output([ environment["git_executable"], "rev-parse", "--short=10", "HEAD" ]).decode("utf-8").strip()
	configuration["project_version"]["branch"] = subprocess.check_output([ environment["git_executable"], "rev-parse", "--abbrev-ref", "HEAD" ]).decode("utf-8").strip()
	configuration["project_version"]["numeric"] = "{identifier}".format(**configuration["project_version"])
	configuration["project_version"]["full"] = "{identifier}-{revision}".format(**configuration["project_version"])

	return configuration

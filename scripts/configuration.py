import subprocess

import commands.clean
import commands.distribute
import commands.lint
import commands.test


def get_command_list():
	return [
		commands.clean,
		commands.distribute,
		commands.lint,
		commands.test,
	]


def load_configuration(environment):
	configuration = {
		"project": "bhamon-build",
		"project_name": "Build Service",
		"project_version": { "identifier": "1.0" },
	}

	configuration["project_version"]["revision"] = subprocess.check_output([ environment["git_executable"], "rev-parse", "--short=10", "HEAD" ]).decode("utf-8").strip()
	configuration["project_version"]["branch"] = subprocess.check_output([ environment["git_executable"], "rev-parse", "--abbrev-ref", "HEAD" ]).decode("utf-8").strip()
	configuration["project_version"]["numeric"] = "{identifier}".format(**configuration["project_version"])
	configuration["project_version"]["full"] = "{identifier}+{revision}".format(**configuration["project_version"])

	configuration["author"] = "Benjamin Hamon"
	configuration["author_email"] = "hamon.benjamin@gmail.com"
	configuration["project_url"] = "https://github.com/BenjaminHamon/BuildService"

	configuration["components"] = [
		{
			"name": "bhamon-build-master",
			"path": "master",
			"packages": [ "bhamon_build_master" ],
			"description": "Master component for build service, responsible for supervising workers and builds",
			"install_requires": [ "websockets" ],
		},
		{
			"name": "bhamon-build-model",
			"path": "model",
			"packages": [ "bhamon_build_model" ],
			"description": "Model library for build service",
		},
		{
			"name": "bhamon-build-service",
			"path": "service",
			"packages": [ "bhamon_build_service" ],
			"description": "Web service component for build service, exposing a web interface to interact with the master",
			"install_requires": [ "flask" ],
		},
		{
			"name": "bhamon-build-website",
			"path": "website",
			"packages": [ "bhamon_build_website" ],
			"description": "Website component for the build service, exposing a web interface for the master",
			"install_requires": [ "flask", "requests" ],
		},
		{
			"name": "bhamon-build-worker",
			"path": "worker",
			"packages": [ "bhamon_build_worker" ],
			"description": "Worker component for build service, responsible for executing builds",
			"install_requires": [ "filelock", "requests", "websockets" ],
		},
	]

	return configuration

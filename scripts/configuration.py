import subprocess

import commands.clean
import commands.develop
import commands.distribute
import commands.lint
import commands.test


def get_command_list():
	return [
		commands.clean,
		commands.develop,
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
			"description": "Master component for build service, responsible for supervising workers and builds",
			"packages": [ "bhamon_build_master" ],
			"dependencies": [ "websockets" ],
		},
		{
			"name": "bhamon-build-model",
			"path": "model",
			"description": "Model library for build service",
			"packages": [ "bhamon_build_model" ],
		},
		{
			"name": "bhamon-build-service",
			"path": "service",
			"description": "Web service component for build service, exposing a web interface to interact with the master",
			"packages": [ "bhamon_build_service" ],
			"dependencies": [ "flask" ],
		},
		{
			"name": "bhamon-build-website",
			"path": "website",
			"description": "Website component for the build service, exposing a web interface for the master",
			"packages": [ "bhamon_build_website" ],
			"dependencies": [ "flask", "requests" ],
		},
		{
			"name": "bhamon-build-worker",
			"path": "worker",
			"description": "Worker component for build service, responsible for executing builds",
			"packages": [ "bhamon_build_worker" ],
			"dependencies": [ "filelock", "requests", "websockets" ],
		},
	]

	return configuration

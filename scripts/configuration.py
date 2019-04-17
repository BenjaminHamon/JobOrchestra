import glob
import os
import subprocess

import scripts.commands.clean
import scripts.commands.develop
import scripts.commands.distribute
import scripts.commands.lint
import scripts.commands.test


def get_command_list():
	return [
		scripts.commands.clean,
		scripts.commands.develop,
		scripts.commands.distribute,
		scripts.commands.lint,
		scripts.commands.test,
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
		},
		{
			"name": "bhamon-build-model",
			"path": "model",
			"packages": [ "bhamon_build_model" ],
		},
		{
			"name": "bhamon-build-service",
			"path": "service",
			"packages": [ "bhamon_build_service" ],
		},
		{
			"name": "bhamon-build-website",
			"path": "website",
			"packages": [ "bhamon_build_website" ],
		},
		{
			"name": "bhamon-build-worker",
			"path": "worker",
			"packages": [ "bhamon_build_worker" ],
		},
	]

	return configuration


def get_setuptools_parameters(configuration):
	return {
		"version": configuration["project_version"]["full"],
		"author": configuration["author"],
		"author_email": configuration["author_email"],
		"url": configuration["project_url"],
	}


def list_package_data(package, pattern_collection):
	all_files = []
	for pattern in pattern_collection:
		all_files += glob.glob(package + "/" + pattern, recursive = True)
	return [ os.path.relpath(path, package) for path in all_files ]

import datetime
import glob
import os
import subprocess

import scripts.commands.artifact
import scripts.commands.clean
import scripts.commands.develop
import scripts.commands.distribute
import scripts.commands.lint
import scripts.commands.release
import scripts.commands.test


def get_command_list():
	return [
		scripts.commands.artifact,
		scripts.commands.clean,
		scripts.commands.develop,
		scripts.commands.distribute,
		scripts.commands.lint,
		scripts.commands.release,
		scripts.commands.test,
	]


def load_configuration(environment):
	configuration = {
		"project": "bhamon-build",
		"project_name": "Build Service",
		"project_version": { "identifier": "1.0" },
	}

	branch = subprocess.check_output([ environment["git_executable"], "rev-parse", "--abbrev-ref", "HEAD" ]).decode("utf-8").strip()
	revision = subprocess.check_output([ environment["git_executable"], "rev-parse", "--short=10", "HEAD" ]).decode("utf-8").strip()
	revision_date = int(subprocess.check_output([ environment["git_executable"], "show", "--no-patch", "--format=%ct", revision ]).decode("utf-8").strip())
	revision_date = datetime.datetime.utcfromtimestamp(revision_date).replace(microsecond = 0).isoformat() + "Z"

	configuration["project_version"]["branch"] = branch
	configuration["project_version"]["revision"] = revision
	configuration["project_version"]["date"] = revision_date
	configuration["project_version"]["numeric"] = "{identifier}".format(**configuration["project_version"])
	configuration["project_version"]["full"] = "{identifier}+{revision}".format(**configuration["project_version"])

	configuration["author"] = "Benjamin Hamon"
	configuration["author_email"] = "hamon.benjamin@gmail.com"
	configuration["project_url"] = "https://github.com/BenjaminHamon/BuildService"
	configuration["copyright"] = "Copyright (c) 2019 Benjamin Hamon"

	configuration["development_dependencies"] = [ "pylint", "pymongo", "pytest", "wheel" ]

	configuration["components"] = [
		{ "name": "bhamon-build-cli", "path": "cli", "packages": [ "bhamon_build_cli" ] },
		{ "name": "bhamon-build-master", "path": "master", "packages": [ "bhamon_build_master" ] },
		{ "name": "bhamon-build-model", "path": "model", "packages": [ "bhamon_build_model" ] },
		{ "name": "bhamon-build-service", "path": "service", "packages": [ "bhamon_build_service" ] },
		{ "name": "bhamon-build-website", "path": "website", "packages": [ "bhamon_build_website" ] },
		{ "name": "bhamon-build-worker", "path": "worker", "packages": [ "bhamon_build_worker" ] },
	]

	if "artifact_repository" in environment:
		configuration["artifact_repository"] = os.path.join(os.path.normpath(environment["artifact_repository"]), "BuildService")

	configuration["filesets"] = {
		"distribution": lambda configuration, parameters: scripts.commands.distribute.create_fileset(next(c for c in configuration["components"] if c["name"] == parameters["component"])),
	}

	configuration["artifacts"] = {
		"package": {
			"file_name": "{project}_{version}_package",
			"path_in_repository": "packages",
			"filesets": [
				{ "identifier": "distribution", "path_in_archive": "bhamon-build-cli", "parameters": { "component": "bhamon-build-cli" } },
				{ "identifier": "distribution", "path_in_archive": "bhamon-build-master", "parameters": { "component": "bhamon-build-master" } },
				{ "identifier": "distribution", "path_in_archive": "bhamon-build-model", "parameters": { "component": "bhamon-build-model" } },
				{ "identifier": "distribution", "path_in_archive": "bhamon-build-service", "parameters": { "component": "bhamon-build-service" } },
				{ "identifier": "distribution", "path_in_archive": "bhamon-build-website", "parameters": { "component": "bhamon-build-website" } },
				{ "identifier": "distribution", "path_in_archive": "bhamon-build-worker", "parameters": { "component": "bhamon-build-worker" } },
			],
		},
	}

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

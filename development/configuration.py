import datetime
import glob
import importlib
import os
import subprocess
import sys


def load_configuration(environment):
	configuration = {
		"project": "bhamon-orchestra",
		"project_name": "Job Orchestra",
		"project_version": { "identifier": "2.0" },
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
	configuration["project_url"] = "https://github.com/BenjaminHamon/JobOrchestra"
	configuration["copyright"] = "Copyright (c) 2019 Benjamin Hamon"

	configuration["development_toolkit"] = "git+https://github.com/BenjaminHamon/DevelopmentToolkit@{revision}#subdirectory=toolkit"
	configuration["development_toolkit_revision"] = "5e12ab4651373b0399201075ea9e78cb0015b091"
	configuration["development_dependencies"] = [ "pylint", "pymongo", "pytest", "pytest-asyncio", "pytest-json", "wheel" ]

	configuration["components"] = [
		{ "name": "bhamon-orchestra-cli", "path": "cli" },
		{ "name": "bhamon-orchestra-master", "path": "master" },
		{ "name": "bhamon-orchestra-model", "path": "model" },
		{ "name": "bhamon-orchestra-service", "path": "service" },
		{ "name": "bhamon-orchestra-website", "path": "website" },
		{ "name": "bhamon-orchestra-worker", "path": "worker" },
	]

	configuration["project_identifier_for_artifact_server"] = "JobOrchestra"

	configuration["filesets"] = {
		"distribution": {
			"path_in_workspace": os.path.join(".artifacts", "distributions", "{component}"),
			"file_functions": [ _list_distribution_files ],
		},
	}

	configuration["artifacts"] = {
		"package": {
			"file_name": "{project}_{version}_package",
			"installation_directory": ".artifacts/distributions",
			"path_in_repository": "packages",

			"filesets": [
				{
					"identifier": "distribution",
					"path_in_archive": component["name"],
					"parameters": {
						"component": component["name"],
					},
				}

				for component in configuration["components"]
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


def load_commands():
	all_modules = [
		"development.commands.artifact",
		"development.commands.clean",
		"development.commands.develop",
		"development.commands.distribute",
		"development.commands.lint",
		"development.commands.release",
		"development.commands.test_distribution",
		"development.commands.test",
	]

	return [ import_command(module) for module in all_modules ]


def import_command(module_name):
	try:
		return {
			"module_name": module_name,
			"module": importlib.import_module(module_name),
		}

	except ImportError:
		return {
			"module_name": module_name,
			"exception": sys.exc_info(),
		}


def _list_distribution_files(path_in_workspace, parameters):
	archive_name = "{component}-{version}-py3-none-any.whl"
	archive_name = archive_name.format(component = parameters["component"].replace("-", "_"), version = parameters["version"])
	return [ os.path.join(path_in_workspace, archive_name) ]

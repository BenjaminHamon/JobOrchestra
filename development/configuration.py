import copy
import datetime
import glob
import importlib
import os
import subprocess
import sys


def load_configuration(environment):
	configuration = {
		"project_identifier": "bhamon-orchestra",
		"project_name": "Job Orchestra",
		"project_version": load_project_version(environment["git_executable"], "4.0"),
	}

	configuration["author"] = "Benjamin Hamon"
	configuration["author_email"] = "hamon.benjamin@gmail.com"
	configuration["project_url"] = "https://github.com/BenjaminHamon/JobOrchestra"
	configuration["project_license"] = "MIT License"
	configuration["project_copyright"] = "Copyright (c) 2021 Benjamin Hamon"

	configuration["development_toolkit"] = "git+https://github.com/BenjaminHamon/DevelopmentToolkit@{revision}#subdirectory=toolkit"
	configuration["development_toolkit_revision"] = "5e12ab4651373b0399201075ea9e78cb0015b091"

	configuration["development_dependencies"] = [ "wheel" ]
	configuration["development_dependencies"] += [ "pylint ~= 2.7.1", "pytest ~= 6.2.2", "pytest-asyncio ~= 0.14.0", "pytest-json ~= 0.4.0" ]
	configuration["development_dependencies"] += [ "pymongo ~= 3.11.3", "psycopg2 ~= 2.8.6", "SQLAlchemy ~= 1.3.23", "SQLAlchemy-Utils == 0.36.7" ]

	configuration["components"] = [
		{ "name": "bhamon-orchestra-cli", "path": "cli" },
		{ "name": "bhamon-orchestra-master", "path": "master" },
		{ "name": "bhamon-orchestra-model", "path": "model" },
		{ "name": "bhamon-orchestra-service", "path": "service" },
		{ "name": "bhamon-orchestra-website", "path": "website" },
		{ "name": "bhamon-orchestra-worker", "path": "worker" },
	]

	configuration["project_identifier_for_artifact_server"] = "JobOrchestra"

	configuration["artifact_directory"] = "artifacts"
	configuration["temporary_directory"] = os.path.join("artifacts", "temporary")

	configuration["filesets"] = load_filesets(configuration)
	configuration["artifacts"] = load_artifacts(configuration)

	return configuration


def load_project_version(git_executable, identifier):
	branch = subprocess.check_output([ git_executable, "rev-parse", "--abbrev-ref", "HEAD" ], universal_newlines = True).strip()
	revision = subprocess.check_output([ git_executable, "rev-parse", "--short=10", "HEAD" ], universal_newlines = True).strip()
	revision_date = int(subprocess.check_output([ git_executable, "show", "--no-patch", "--format=%ct", revision ], universal_newlines = True).strip())
	revision_date = datetime.datetime.utcfromtimestamp(revision_date).replace(microsecond = 0).isoformat() + "Z"

	return {
		"identifier": identifier,
		"numeric": identifier,
		"full": identifier + "+" + revision,
		"branch": branch,
		"revision": revision,
		"date": revision_date,
	}


def load_filesets(configuration):
	return {
		"distribution": {
			"path_in_workspace": os.path.join(configuration["artifact_directory"], "distributions", "{component}"),
			"file_functions": [ _list_distribution_files ],
		},

		"test_results": {
			"path_in_workspace": os.path.join(configuration["artifact_directory"], "test_results"),
			"file_patterns": [ "**" ],
		},
	}


def load_artifacts(configuration):
	return {
		"package": {
			"file_name": "{project}_{version}+{revision}_package",
			"installation_directory": os.path.join(configuration["artifact_directory"], "distributions"),
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

		"test_results": {
			"file_name": "{project}_{version}+{revision}_test-results_{run}",
			"installation_directory": os.path.join(configuration["artifact_directory"], "test_results"),
			"path_in_repository": "test_results",

			"filesets": [
				{ "identifier": "test_results", "path_in_archive": ".", },
			],
		}
	}


def get_setuptools_parameters(configuration):
	return {
		"version": configuration["project_version"]["full"],
		"author": configuration["author"],
		"author_email": configuration["author_email"],
		"url": configuration["project_url"],
		"license": configuration["project_license"],
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
		"development.commands.info",
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
	parameters = copy.deepcopy(parameters)
	parameters["component"] = parameters["component"].replace("-", "_")
	archive_name = "{component}-{version}+{revision}-py3-none-any.whl".format(**parameters)
	return [ os.path.join(path_in_workspace, archive_name) ]

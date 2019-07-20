import argparse
import copy
import filecmp
import glob
import logging
import os
import shutil
import zipfile

import scripts.configuration


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument

	def parse_key_value_parameter(argument_value):
		key_value = argument_value.split("=")
		if len(key_value) != 2:
			raise argparse.ArgumentTypeError("invalid key value parameter: '%s'" % argument_value)
		return (key_value[0], key_value[1])

	command_list = [ "show", "package", "verify", "upload" ]

	parser = subparsers.add_parser("artifact", formatter_class = argparse.RawTextHelpFormatter,
		help = "execute commands related to build artifacts")
	parser.add_argument("artifact", choices = configuration["artifacts"].keys(),
		metavar = "<artifact>", help = "set an artifact definition to use for the commands")
	parser.add_argument("--command", choices = command_list, required = True, nargs = "+", dest = "artifact_commands",
		metavar = "<command>", help = "set the command(s) to execute for the artifact" + "\n" + "(%s)" % ", ".join(command_list))
	parser.add_argument("--parameters", nargs = "*", type = parse_key_value_parameter, default = [],
		metavar = "<key=value>", help = "set parameters for the artifact")
	parser.add_argument("--force", action = "store_true", help = "(upload only) if the artifact already exists, overwrite it")
	return parser


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	parameters = {
		"project": configuration["project"],
		"version": configuration["project_version"]["full"],
	}

	parameters.update(arguments.parameters)

	artifact = configuration["artifacts"][arguments.artifact]
	artifact_name = artifact["file_name"].format(**parameters)
	local_artifact_path = os.path.join(".artifacts", artifact["path_in_repository"], artifact_name)

	if "upload" in arguments.artifact_commands:
		artifact_repository = os.path.normpath(environment["artifact_repository"])
		remote_artifact_path = os.path.join(artifact_repository, configuration["project"], artifact["path_in_repository"], artifact_name)

	if "show" in arguments.artifact_commands:
		artifact_files = list_artifact_files(artifact, configuration, parameters)
		show(artifact_name, artifact_files)
		print("")
	if "package" in arguments.artifact_commands:
		artifact_files = merge_artifact_mapping(map_artifact_files(artifact, configuration, parameters))
		package(local_artifact_path, artifact_files, arguments.simulate)
		print("")
	if "verify" in arguments.artifact_commands:
		verify(local_artifact_path)
		print("")
	if "upload" in arguments.artifact_commands:
		upload(local_artifact_path, remote_artifact_path, arguments.force, arguments.simulate, arguments.results)
		print("")


def show(artifact_name, artifact_files):
	logger.info("Artifact %s", artifact_name)

	for file_path in artifact_files:
		logger.info("%s", file_path)


def package(artifact_path, artifact_files, simulate):
	logger.info("Packaging artifact '%s'", artifact_path)

	artifact_directory = os.path.dirname(artifact_path)
	if not simulate and not os.path.isdir(artifact_directory):
		os.makedirs(artifact_directory)

	if len(artifact_files) == 0:
		raise RuntimeError("The artifact is empty")

	if simulate:
		for source, destination in artifact_files:
			logger.info("%s => %s", source, destination)
	else:
		with zipfile.ZipFile(artifact_path + ".zip.tmp", "w", zipfile.ZIP_DEFLATED) as artifact_file:
			for source, destination in artifact_files:
				logger.info("%s => %s", source, destination)
				artifact_file.write(source, destination)
		shutil.move(artifact_path + ".zip.tmp", artifact_path + ".zip")


def verify(artifact_path):
	logger.info("Verifying artifact '%s'", artifact_path)

	with zipfile.ZipFile(artifact_path + ".zip", 'r') as artifact_file:
		if artifact_file.testzip():
			raise RuntimeError('Artifact package is corrupted')


def upload(local_artifact_path, remote_artifact_path, overwrite, simulate, result_file_path):
	logger.info("Uploading artifact '%s' to '%s'", local_artifact_path, remote_artifact_path)

	remote_artifact_directory = os.path.dirname(remote_artifact_path)
	if not simulate and not os.path.isdir(remote_artifact_directory):
		os.makedirs(remote_artifact_directory)

	if os.path.exists(remote_artifact_path + ".zip") and not overwrite:
		raise ValueError("Artifact already exists in repository (Path: '%s')" % remote_artifact_path)

	if not simulate:
		shutil.copyfile(local_artifact_path + ".zip", remote_artifact_path + ".zip.tmp")
		shutil.move(remote_artifact_path + ".zip.tmp", remote_artifact_path + ".zip")

	if result_file_path:
		results = scripts.configuration.load_results(result_file_path)
		results["artifacts"].append({ "name": os.path.basename(remote_artifact_path), "path": remote_artifact_path + ".zip" })
		if not simulate:
			scripts.configuration.save_results(result_file_path, results)


def list_artifact_files(artifact, configuration, parameters):
	all_files = []

	for fileset_options in artifact["filesets"]:
		fileset = configuration["filesets"][fileset_options["identifier"]]
		fileset_parameters = copy.deepcopy(fileset_options.get("parameters", {}))
		fileset_parameters.update(parameters)

		if callable(fileset):
			fileset = fileset(configuration, fileset_parameters)

		all_files += load_fileset(fileset, fileset_parameters)

	all_files.sort()

	return all_files


def map_artifact_files(artifact, configuration, parameters):
	all_files = []

	for fileset_options in artifact["filesets"]:
		fileset = configuration["filesets"][fileset_options["identifier"]]
		fileset_parameters = copy.deepcopy(fileset_options.get("parameters", {}))
		fileset_parameters.update(parameters)

		if callable(fileset):
			fileset = fileset(configuration, fileset_parameters)

		path_in_workspace = fileset["path_in_workspace"].format(**fileset_parameters)
		for source in load_fileset(fileset, fileset_parameters):
			destination = source
			if "path_in_archive" in fileset_options:
				destination = os.path.join(fileset_options["path_in_archive"], os.path.relpath(source, path_in_workspace))
			all_files.append((source, destination.replace("\\", "/")))

	all_files.sort()

	return all_files


def merge_artifact_mapping(artifact_files):
	merged_files = []
	has_conflicts = False

	for destination in set(dst for src, dst in artifact_files):
		source_collection = [ src for src, dst in artifact_files if dst == destination ]
		for source in source_collection[1:]:
			if not filecmp.cmp(source_collection[0], source):
				has_conflicts = True
				logger.error("Mapping conflict: %s, %s => %s", source_collection[0], source, destination)
		merged_files.append((source_collection[0], destination))

	if has_conflicts:
		raise ValueError("Artifact mapper has conflicts")

	merged_files.sort()

	return merged_files


def load_fileset(fileset, parameters):
	all_files = []
	path_in_workspace = fileset["path_in_workspace"].format(**parameters)
	for file_pattern in fileset["file_patterns"]:
		all_files += glob.glob(os.path.join(path_in_workspace, file_pattern.format(**parameters)))
	return sorted(file_path.replace("\\", "/") for file_path in all_files)
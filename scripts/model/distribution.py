import glob
import logging
import os
import re
import shutil
import subprocess


logger = logging.getLogger("Distribution")

file_url_regex = re.compile(r"^file:///(?P<path>([a-zA-Z]:)?[a-zA-Z0-9_\-\./]+)$")
ssh_url_regex = re.compile(r"^ssh://(?P<user>[a-zA-Z0-9_\-]+)@(?P<host>[a-zA-Z0-9_\-\.]+):(?P<path>[a-zA-Z0-9_\-\./]+)$")


def create_repository_client(server_url, server_parameters, environment):
	if server_url.startswith("file://"):
		return PythonPackageRepositoryFileClient(**file_url_regex.search(server_url).groupdict())

	if server_url.startswith("ssh://"):
		client = PythonPackageRepositorySshClient(**ssh_url_regex.search(server_url).groupdict())
		client.ssh_executable = environment["ssh_executable"]
		client.scp_executable = environment["scp_executable"]
		client.ssh_parameters = server_parameters.get("ssh_parameters", [])
		return client

	raise ValueError("Unsupported server url: '%s'" % server_url)



class PythonPackageRepositoryFileClient:


	def __init__(self, path):
		self.server_path = os.path.normpath(path)


	def search(self, distribution, version_pattern, file_extension):
		distribution_pattern = distribution.replace("-", "_") + "-" + version_pattern + file_extension
		return next((x for x in glob.glob(os.path.join(self.server_path, distribution, distribution_pattern))), None)


	def create_directory(self, distribution, simulate):
		directory_path = os.path.join(self.server_path, distribution)
		if not simulate:
			os.makedirs(directory_path, exist_ok = True)


	def upload(self, local_directory, distribution, version, file_extension, simulate): # pylint: disable = too-many-arguments
		logger.info("Uploading distribution '%s' to repository '%s'", distribution, self.server_path)

		archive_name = distribution.replace("-", "_") + "-" + version["full"]
		source_path = os.path.join(local_directory, distribution, archive_name + file_extension)
		destination_path = os.path.join(self.server_path, distribution, archive_name + file_extension)

		if not simulate and not os.path.exists(source_path):
			raise FileNotFoundError("Local file does not exist: '%s'" % source_path)

		existing_distribution = self.search(distribution, version["identifier"] + "+*", file_extension)
		if existing_distribution is not None:
			raise ValueError("Version %s already exists: '%s'" % (version["identifier"], os.path.basename(existing_distribution)))

		self.create_directory(distribution, simulate)

		logger.info("Copying '%s' to '%s'", source_path, destination_path)
		if not simulate:
			shutil.copyfile(source_path, destination_path + ".tmp")
			shutil.move(destination_path + ".tmp", destination_path)



class PythonPackageRepositorySshClient:


	def __init__(self, user, host, path):
		self.server_user = user
		self.server_host = host
		self.server_path = path

		self.ssh_executable = "ssh"
		self.scp_executable = "scp"
		self.ssh_parameters = []


	def search(self, distribution, version_pattern, file_extension):
		distribution_pattern = distribution.replace("-", "_") + "-" + version_pattern + file_extension
		search_command = [ self.ssh_executable ] + self.ssh_parameters + [ self.server_user + "@" + self.server_host ]
		search_command += [ "ls %s" % (self.server_path + "/" + distribution + "/" + distribution_pattern) ]

		logger.info("+ %s", " ".join(("'" + x + "'") if " " in x else x for x in search_command))
		search_process = subprocess.Popen(search_command, stdout = subprocess.PIPE)
		search_process.wait()

		if search_process.returncode == 255:
			raise RuntimeError("Failed to connect to the SSH server")
		if search_process.returncode != 0:
			return None
		return search_process.stdout.read().decode().splitlines()[0]


	def create_directory(self, distribution, simulate):
		mkdir_command = [ self.ssh_executable ] + self.ssh_parameters + [ self.server_user + "@" + self.server_host ]
		mkdir_command += [ "mkdir --parents %s" % (self.server_path + "/" + distribution) ]

		logger.info("+ %s", " ".join(("'" + x + "'") if " " in x else x for x in mkdir_command))
		if not simulate:
			mkdir_result = subprocess.call(mkdir_command)
			if mkdir_result == 255:
				raise RuntimeError("Failed to connect to the SSH server")
			if mkdir_result != 0:
				raise RuntimeError("Failed to create directory: '%s'" % distribution)


	def upload(self, local_directory, distribution, version, file_extension, simulate): # pylint: disable = too-many-arguments
		logger.info("Uploading distribution '%s' to repository '%s'", distribution, "ssh://" + self.server_host + ":" + self.server_path)

		archive_name = distribution.replace("-", "_") + "-" + version["full"]
		source_path = os.path.join(local_directory, distribution, archive_name + file_extension)
		destination_path = self.server_path + "/" + distribution + "/" + archive_name + file_extension

		if not simulate and not os.path.exists(source_path):
			raise FileNotFoundError("Local file does not exist: '%s'" % source_path)

		existing_distribution = self.search(distribution, version["identifier"] + "+*", file_extension)
		if existing_distribution is not None:
			raise ValueError("Version %s already exists: '%s'" % (version["identifier"], os.path.basename(existing_distribution)))

		self.create_directory(distribution, simulate)

		upload_command = [ self.scp_executable ] + self.ssh_parameters + [ source_path ]
		upload_command += [ self.server_user + "@" + self.server_host + ":" + destination_path + ".tmp" ]

		logger.info("+ %s", " ".join(("'" + x + "'") if " " in x else x for x in upload_command))
		if not simulate:
			upload_result = subprocess.call(upload_command)
			if upload_result == 255:
				raise RuntimeError("Failed to connect to the SSH server")
			if upload_result != 0:
				raise RuntimeError("Failed to upload the artifact")

		move_command = [ self.ssh_executable ] + self.ssh_parameters + [ self.server_user + "@" + self.server_host ]
		move_command += [ "mv %s %s" % (destination_path + ".tmp", destination_path) ]

		logger.info("+ %s", " ".join(("'" + x + "'") if " " in x else x for x in move_command))
		if not simulate:
			move_result = subprocess.call(move_command)
			if move_result == 255:
				raise RuntimeError("Failed to connect to the SSH server")
			if move_result != 0:
				raise RuntimeError("Failed to upload the artifact")

import json
import os
import platform
import signal
import subprocess
import sys
import time

import pymongo

from bhamon_build_model.authentication_provider import AuthenticationProvider
from bhamon_build_model.authorization_provider import AuthorizationProvider
from bhamon_build_model.run_provider import RunProvider
from bhamon_build_model.database.file_storage import FileStorage
from bhamon_build_model.job_provider import JobProvider
from bhamon_build_model.task_provider import TaskProvider
from bhamon_build_model.user_provider import UserProvider
from bhamon_build_model.worker_provider import WorkerProvider

from . import environment


shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGINT # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0


class Context:


	def __init__(self, temporary_directory, database_type):
		environment_instance = environment.load_test_context_environment(str(temporary_directory), database_type)

		self.temporary_directory = str(temporary_directory)
		self.master_address = environment_instance["master_address"]
		self.master_port = environment_instance["master_port"]
		self.service_address = environment_instance["service_address"]
		self.service_port = environment_instance["service_port"]
		self.website_address = environment_instance["website_address"]
		self.website_port = environment_instance["website_port"]
		self.database_uri = environment_instance["database_uri"]
		self.process_collection = []


	def __enter__(self):
		if self.database_uri is not None and self.database_uri.startswith("mongodb://"):
			database_client = pymongo.MongoClient(self.database_uri, serverSelectionTimeoutMS = 5000)
			database_client.drop_database(database_client.get_database())
			database_client.close()
		return self


	def __exit__(self, exception_type, exception_value, traceback):
		if self.database_uri is not None and self.database_uri.startswith("mongodb://"):
			database_client = pymongo.MongoClient(self.database_uri)
			database_client.drop_database(database_client.get_database())
			database_client.close()
		for process in self.process_collection:
			os.kill(process.pid, shutdown_signal)
			try:
				process.wait(5)
			except subprocess.TimeoutExpired:
				process.kill()
		self.process_collection.clear()


	def get_service_uri(self):
		return "http://%s:%s" % (self.service_address, self.service_port)


	def get_website_uri(self):
		return "http://%s:%s" % (self.website_address, self.website_port)


	def invoke_master(self):
		return self.invoke(
			identifier = "master",
			script = "master_main.py",
			arguments = [ "--address", self.master_address, "--port", str(self.master_port), "--database", self.database_uri ],
			workspace = os.path.join(self.temporary_directory, "master"),
		)


	def invoke_worker(self, worker_identifier):
		return self.invoke(
			identifier = worker_identifier,
			script = "worker_main.py",
			arguments = [ "--identifier", worker_identifier, "--master-uri", "ws://%s:%s" % (self.master_address, self.master_port) ],
			workspace = os.path.join(self.temporary_directory, worker_identifier),
		)


	def invoke_executor(self, worker_identifier, job_identifier, run_identifier):
		worker_directory = os.path.join(self.temporary_directory, worker_identifier)
		executor_run_directory = os.path.join(worker_directory, "runs", job_identifier + "_" + run_identifier)

		os.makedirs(executor_run_directory)

		return self.invoke(
			identifier = worker_identifier + "_" + "executor",
			script = "executor_main.py",
			arguments = [ job_identifier, run_identifier ],
			workspace = worker_directory,
		)


	def invoke_service(self):
		return self.invoke(
			identifier = "service",
			script = "service_main.py",
			arguments = [ "--address", self.service_address, "--port", str(self.service_port), "--database", self.database_uri ],
			workspace = os.path.join(self.temporary_directory, "master"),
		)


	def invoke_website(self):
		return self.invoke(
			identifier = "website",
			script = "website_main.py",
			arguments = [ "--address", self.website_address, "--port", str(self.website_port) ],
			workspace = os.path.join(self.temporary_directory, "website"),
		)


	def invoke(self, identifier, script, arguments, workspace):
		script_root = os.path.dirname(os.path.realpath(__file__))
		command = [ sys.executable, os.path.join(script_root, script) ] + arguments

		os.makedirs(workspace, exist_ok = True)

		with open(os.path.join(self.temporary_directory, identifier + "_" + "stdout.log"), mode = "w") as stdout_file:
			with open(os.path.join(self.temporary_directory, identifier + "_" + "stderr.log"), mode = "w") as stderr_file:
				process = subprocess.Popen(command, cwd = workspace, stdout = stdout_file, stderr = stderr_file, creationflags = subprocess_flags)

		self.process_collection.append(process)

		time.sleep(1) # Wait for initialization

		return {
			"identifier": identifier,
			"process": process,
			"stdout_file_path": os.path.join(self.temporary_directory, identifier + "_" + "stdout.log"),
			"stderr_file_path": os.path.join(self.temporary_directory, identifier + "_" + "stderr.log"),
		}


	def configure_worker_authentication(self, worker_collection):
		providers = self.instantiate_providers()
		user = providers["user"].create("worker", "Worker")
		providers["user"].update_roles(user, "Worker")
		token = providers["authentication"].create_token("worker", None, None)

		for worker in worker_collection:
			worker_directory = os.path.join(self.temporary_directory, worker)
			os.makedirs(worker_directory, exist_ok = True)
			with open(os.path.join(worker_directory, "authentication.json"), "w") as authentication_file:
				json.dump(token, authentication_file, indent = 4)


	def configure_website_authentication(self):
		providers = self.instantiate_providers()
		user = providers["user"].create("viewer", "viewer")
		providers["user"].update_roles(user, [ "Viewer" ])
		providers["authentication"].set_password("viewer", "password")
		return ("viewer", "password")


	def instantiate_providers(self):
		database_client_instance = environment.create_database_client(self.database_uri)
		file_storage_instance = FileStorage(os.path.join(self.temporary_directory, "master"))

		return {
			"authentication": AuthenticationProvider(database_client_instance),
			"authorization": AuthorizationProvider(),
			"run": RunProvider(database_client_instance, file_storage_instance),
			"job": JobProvider(database_client_instance),
			"task": TaskProvider(database_client_instance),
			"user": UserProvider(database_client_instance),
			"worker": WorkerProvider(database_client_instance),
		}

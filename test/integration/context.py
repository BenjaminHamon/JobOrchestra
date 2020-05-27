import json
import os
import platform
import signal
import subprocess
import sys
import time

import pymongo

from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.database.file_storage import FileStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.user_provider import UserProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider

from . import environment


shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGINT # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0



class DatabaseContext:


	def __init__(self, temporary_directory, database_type):
		environment_instance = environment.load_test_context_environment(str(temporary_directory), database_type)

		self.temporary_directory = str(temporary_directory)
		self.database_uri = environment_instance["database_uri"]
		self.database_client = environment.create_database_client(self.database_uri)
		self.database_administration = environment.create_database_administration(self.database_uri)


	def __enter__(self):
		if self.database_uri.startswith("mongodb://"):
			with pymongo.MongoClient(self.database_uri, serverSelectionTimeoutMS = 5000) as mongo_client:
				mongo_client.drop_database(mongo_client.get_database())

		return self


	def __exit__(self, exception_type, exception_value, traceback):
		self.database_administration.close()
		self.database_client.close()

		if self.database_uri.startswith("mongodb://"):
			with pymongo.MongoClient(self.database_uri, serverSelectionTimeoutMS = 5000) as mongo_client:
				mongo_client.drop_database(mongo_client.get_database())



class OrchestraContext: # pylint: disable = too-many-instance-attributes


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

		if self.database_uri is not None:
			date_time_provider_instance = DateTimeProvider()

			self.database_client = environment.create_database_client(self.database_uri)
			self.file_storage = FileStorage(os.path.join(self.temporary_directory, "master"))

			self.authentication_provider = AuthenticationProvider(self.database_client, date_time_provider_instance)
			self.authorization_provider = AuthorizationProvider()
			self.job_provider = JobProvider(self.database_client, date_time_provider_instance)
			self.project_provider = ProjectProvider(self.database_client, date_time_provider_instance)
			self.run_provider = RunProvider(self.database_client, self.file_storage, date_time_provider_instance)
			self.schedule_provider = ScheduleProvider(self.database_client, date_time_provider_instance)
			self.user_provider = UserProvider(self.database_client, date_time_provider_instance)
			self.worker_provider = WorkerProvider(self.database_client, date_time_provider_instance)


	def __enter__(self):
		if self.database_uri is not None and self.database_uri.startswith("mongodb://"):
			with pymongo.MongoClient(self.database_uri, serverSelectionTimeoutMS = 5000) as mongo_client:
				mongo_client.drop_database(mongo_client.get_database())

		if self.database_uri is not None:
			database_administration = environment.create_database_administration(self.database_uri)
			database_administration.initialize(simulate = False)
			database_administration.close()

		return self


	def __exit__(self, exception_type, exception_value, traceback):
		for process in self.process_collection:
			if process.poll() is None:
				os.kill(process.pid, shutdown_signal)
				try:
					process.wait(5)
				except subprocess.TimeoutExpired:
					process.kill()

		self.process_collection.clear()

		if self.database_uri is not None:
			self.database_client.close()

		if self.database_uri is not None and self.database_uri.startswith("mongodb://"):
			with pymongo.MongoClient(self.database_uri, serverSelectionTimeoutMS = 5000) as mongo_client:
				mongo_client.drop_database(mongo_client.get_database())


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


	def invoke_executor(self, worker_identifier, run_identifier):
		worker_directory = os.path.join(self.temporary_directory, worker_identifier)
		executor_run_directory = os.path.join(worker_directory, "runs", run_identifier)

		os.makedirs(executor_run_directory)

		return self.invoke(
			identifier = worker_identifier + "_" + "executor",
			script = "executor_main.py",
			arguments = [ run_identifier ],
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

		with open(os.path.join(self.temporary_directory, identifier + "_" + "stdout.log"), mode = "w", encoding = "utf-8") as stdout_file:
			with open(os.path.join(self.temporary_directory, identifier + "_" + "stderr.log"), mode = "w", encoding = "utf-8") as stderr_file:
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
		user = self.user_provider.create("worker", "Worker")
		self.user_provider.update_roles(user, "Worker")
		token = self.authentication_provider.create_token("worker", None, None)

		for worker in worker_collection:
			worker_directory = os.path.join(self.temporary_directory, worker)
			os.makedirs(worker_directory, exist_ok = True)
			with open(os.path.join(worker_directory, "authentication.json"), mode = "w", encoding = "utf-8") as authentication_file:
				json.dump(token, authentication_file, indent = 4)


	def configure_service_authentication(self, user_identifier, user_roles):
		user = self.user_provider.create(user_identifier, user_identifier)
		self.user_provider.update_roles(user, user_roles)
		token = self.authentication_provider.create_token(user_identifier, None, None)
		return (user_identifier, token["secret"])


	def configure_website_authentication(self, user_identifier, user_roles):
		user = self.user_provider.create(user_identifier, user_identifier)
		self.user_provider.update_roles(user, user_roles)
		self.authentication_provider.set_password(user_identifier, "password")
		return (user_identifier, "password")

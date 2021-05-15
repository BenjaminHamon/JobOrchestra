import logging
import os
import platform
import signal
import subprocess
import sys
import time

import pymongo
import sqlalchemy
import sqlalchemy_utils

from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
import bhamon_orchestra_model.database.sql_database_model as sql_database_model
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer
from bhamon_orchestra_model.users.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.users.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.users.user_provider import UserProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider
from bhamon_orchestra_worker.worker_storage import WorkerStorage

from . import environment
from . import factory


logger = logging.getLogger("Context")

shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGTERM # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0

termination_timeout_seconds = 5


class DatabaseContext:


	def __init__(self, temporary_directory, database_type, database_suffix = None, metadata_factory = None):
		environment_instance = environment.load_test_context_environment(str(temporary_directory), database_type)

		self.temporary_directory = str(temporary_directory)
		self.database_uri = environment_instance["database_uri"] + (("_" + database_suffix) if database_suffix else "")
		self.metadata = None

		if self.database_uri.startswith("postgresql://"):
			self.metadata = metadata_factory()

		self.database_administration_factory = factory.create_database_administration_factory(self.database_uri, self.metadata)
		self.database_client_factory = factory.create_database_client_factory(self.database_uri, self.metadata)


	def __enter__(self):
		if self.database_uri.startswith("mongodb://"):
			with pymongo.MongoClient(self.database_uri, serverSelectionTimeoutMS = 5000) as mongo_client:
				mongo_client.drop_database(mongo_client.get_database())

		if self.database_uri.startswith("postgresql://"):
			if sqlalchemy_utils.database_exists(self.database_uri):
				sqlalchemy_utils.drop_database(self.database_uri)
			sqlalchemy_utils.create_database(self.database_uri)

			database_engine = sqlalchemy.create_engine(self.database_uri)
			self.metadata.create_all(database_engine)
			database_engine.dispose()

		return self


	def __exit__(self, exception_type, exception_value, traceback):
		if self.database_uri.startswith("mongodb://"):
			with pymongo.MongoClient(self.database_uri, serverSelectionTimeoutMS = 5000) as mongo_client:
				mongo_client.drop_database(mongo_client.get_database())

		if self.database_uri.startswith("postgresql://"):
			if sqlalchemy_utils.database_exists(self.database_uri):
				sqlalchemy_utils.drop_database(self.database_uri)



class OrchestraContext: # pylint: disable = too-many-instance-attributes


	def __init__(self, temporary_directory, database_type, database_suffix = None):
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
			self.database_uri += ("_" + database_suffix) if database_suffix else ""

			date_time_provider_instance = DateTimeProvider()

			self.database_administration_factory = factory.create_database_administration_factory(self.database_uri, sql_database_model.metadata)
			self.database_client_factory = factory.create_database_client_factory(self.database_uri, sql_database_model.metadata)
			self.data_storage = FileDataStorage(os.path.join(self.temporary_directory, "master"))

			self.authentication_provider = AuthenticationProvider(date_time_provider_instance)
			self.authorization_provider = AuthorizationProvider()
			self.job_provider = JobProvider(date_time_provider_instance)
			self.project_provider = ProjectProvider(date_time_provider_instance)
			self.run_provider = RunProvider(self.data_storage, date_time_provider_instance)
			self.schedule_provider = ScheduleProvider(date_time_provider_instance)
			self.user_provider = UserProvider(date_time_provider_instance)
			self.worker_provider = WorkerProvider(date_time_provider_instance)


	def __enter__(self):
		if self.database_uri is not None and self.database_uri.startswith("mongodb://"):
			with pymongo.MongoClient(self.database_uri, serverSelectionTimeoutMS = 5000) as mongo_client:
				mongo_client.drop_database(mongo_client.get_database())

		if self.database_uri is not None and self.database_uri.startswith("postgresql://"):
			if sqlalchemy_utils.database_exists(self.database_uri):
				sqlalchemy_utils.drop_database(self.database_uri)
			sqlalchemy_utils.create_database(self.database_uri)

		if self.database_uri is not None:
			with self.database_administration_factory() as database_administration:
				database_administration.initialize(simulate = False)

		return self


	def __exit__(self, exception_type, exception_value, traceback):
		for process in self.process_collection:
			self.terminate(str(process.pid), process, "ContextExit")

		self.process_collection.clear()

		if self.database_uri is not None and self.database_uri.startswith("mongodb://"):
			with pymongo.MongoClient(self.database_uri, serverSelectionTimeoutMS = 5000) as mongo_client:
				mongo_client.drop_database(mongo_client.get_database())

		if self.database_uri is not None and self.database_uri.startswith("postgresql://"):
			if sqlalchemy_utils.database_exists(self.database_uri):
				sqlalchemy_utils.drop_database(self.database_uri)


	def get_service_uri(self):
		return "http://%s:%s" % (self.service_address, self.service_port)


	def get_website_uri(self):
		return "http://%s:%s" % (self.website_address, self.website_port)


	def invoke_master(self):
		return self.invoke(
			identifier = "master",
			module = "test.integration.master_main",
			arguments = [ "--address", self.master_address, "--port", str(self.master_port), "--database", self.database_uri ],
			workspace = os.path.join(self.temporary_directory, "master"),
		)


	def invoke_worker(self, worker_identifier):
		return self.invoke(
			identifier = worker_identifier,
			module = "test.integration.worker_main",
			arguments = [ "--identifier", worker_identifier, "--master-uri", "ws://%s:%s" % (self.master_address, self.master_port) ],
			workspace = os.path.join(self.temporary_directory, worker_identifier),
		)


	def invoke_executor(self, worker_identifier, run_request):
		worker_directory = os.path.join(self.temporary_directory, worker_identifier)
		file_data_storage_instance = FileDataStorage(worker_directory)
		serializer_instance = JsonSerializer(indent = 4)
		worker_storage_instance = WorkerStorage(file_data_storage_instance, serializer_instance)

		worker_storage_instance.create_run(run_request["run_identifier"])
		worker_storage_instance.save_request(run_request["run_identifier"], run_request)

		return self.invoke(
			identifier = worker_identifier + "_" + "executor",
			module = "test.integration.executor_main",
			arguments = [ run_request["run_identifier"] ],
			workspace = worker_directory,
		)


	def invoke_service(self):
		return self.invoke(
			identifier = "service",
			module = "test.integration.service_main",
			arguments = [ "--address", self.service_address, "--port", str(self.service_port), "--database", self.database_uri ],
			workspace = os.path.join(self.temporary_directory, "master"),
		)


	def invoke_website(self):
		return self.invoke(
			identifier = "website",
			module = "test.integration.website_main",
			arguments = [ "--address", self.website_address, "--port", str(self.website_port) ],
			workspace = os.path.join(self.temporary_directory, "website"),
		)


	def invoke(self, identifier, module, arguments, workspace):
		logger.info("Invoking subprocess '%s'", identifier)

		command = [ sys.executable, "-m", module ] + arguments

		process_environment = os.environ.copy()
		process_environment["PYTHONPATH"] = os.getcwd()

		output_log_file_path = os.path.join(self.temporary_directory, identifier + "_" + "stdout.log")
		error_log_file_path = os.path.join(self.temporary_directory, identifier + "_" + "stderr.log")

		os.makedirs(workspace, exist_ok = True)

		with open(output_log_file_path, mode = "a", encoding = "utf-8") as stdout_file:
			with open(error_log_file_path, mode = "a", encoding = "utf-8") as stderr_file:
				process = subprocess.Popen(command, cwd = workspace, env = process_environment,
						stdout = stdout_file, stderr = stderr_file, creationflags = subprocess_flags)

		logger.info("New subprocess '%s' (PID: %s)", identifier, process.pid)

		self.process_collection.append(process)

		time.sleep(1) # Wait for initialization

		return {
			"identifier": identifier,
			"process": process,
			"stdout_file_path": os.path.join(self.temporary_directory, identifier + "_" + "stdout.log"),
			"stderr_file_path": os.path.join(self.temporary_directory, identifier + "_" + "stderr.log"),
		}


	def terminate(self, identifier, process, reason):
		if process not in self.process_collection:
			raise ValueError("Unknown process '%s' (PID: %s)" % (identifier, process.pid))

		logger.info("Terminating subprocess '%s' (PID: %s, Reason: '%s')", identifier, process.pid, reason)

		if process.poll() is None:
			logger.info("Requesting subprocess '%s' for termination (PID: %s)", identifier, process.pid)
			os.kill(process.pid, shutdown_signal)

			try:
				process.wait(termination_timeout_seconds)
			except subprocess.TimeoutExpired:
				pass

		if process.poll() is None:
			logger.error("Forcing subprocess '%s' termination (PID: %s)", identifier, process.pid)
			process.kill()

			try:
				process.wait(termination_timeout_seconds)
			except subprocess.TimeoutExpired:
				pass

		if process.poll() is None:
			logger.error("Terminating subprocess '%s' failed (PID: %s)", identifier, process.pid)

		if process.poll() is not None:
			logger.info("Terminating subprocess '%s' succeeded (PID: %s)", identifier, process.pid)


	def configure_worker_authentication(self, worker_collection):
		serializer_instance = JsonSerializer(indent = 4)

		with self.database_client_factory() as database_client:
			user = self.user_provider.create(database_client, "worker", "Worker")
			self.user_provider.update_roles(database_client, user, "Worker")
			token = self.authentication_provider.create_token(database_client, "worker", None, None)

		for worker in worker_collection:
			worker_directory = os.path.join(self.temporary_directory, worker)
			os.makedirs(worker_directory, exist_ok = True)
			serializer_instance.serialize_to_file(os.path.join(worker_directory, "authentication.json"), token)


	def configure_service_authentication(self, user_identifier, user_roles):
		with self.database_client_factory() as database_client:
			user = self.user_provider.create(database_client, user_identifier, user_identifier)
			self.user_provider.update_roles(database_client, user, user_roles)
			token = self.authentication_provider.create_token(database_client, user_identifier, None, None)

		return (user_identifier, token["secret"])


	def configure_website_authentication(self, user_identifier, user_roles):
		with self.database_client_factory() as database_client:
			user = self.user_provider.create(database_client, user_identifier, user_identifier)
			self.user_provider.update_roles(database_client, user, user_roles)
			self.authentication_provider.set_password(database_client, user_identifier, "password")

		return (user_identifier, "password")

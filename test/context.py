import os
import platform
import signal
import subprocess
import sys
import time
import uuid

import pymongo

import bhamon_build_model.build_provider as build_provider
import bhamon_build_model.file_storage as file_storage
import bhamon_build_model.job_provider as job_provider
import bhamon_build_model.json_database_client as json_database_client
import bhamon_build_model.mongo_database_client as mongo_database_client
import bhamon_build_model.task_provider as task_provider
import bhamon_build_model.worker_provider as worker_provider

import environment


shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGINT
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0


class Context:


	def __init__(self, temporary_directory):
		self.temporary_directory = str(temporary_directory)
		self.master_address = environment.master_address
		self.master_port = environment.master_port
		self.service_address = environment.service_address
		self.service_port = environment.service_port
		self.website_address = environment.website_address
		self.website_port = environment.website_port
		self.database_uri = environment.database_uri
		self.database_name = "test_build_database_" + str(uuid.uuid4())
		self.process_collection = []

		if self.database_uri.startswith("mongodb://"):
			self.database_uri += self.database_name


	def __enter__(self):
		if self.database_uri.startswith("mongodb://"):
			database_client = pymongo.MongoClient(self.database_uri)
			database_client.drop_database(self.database_name)
			database_client.close()
		return self


	def __exit__(self, exception_type, exception_value, traceback):
		if self.database_uri.startswith("mongodb://"):
			database_client = pymongo.MongoClient(self.database_uri)
			database_client.drop_database(self.database_name)
			database_client.close()
		for process in self.process_collection:
			os.kill(process.pid, shutdown_signal)
			try:
				process.wait(5)
			except subprocess.TimeoutExpired:
				process.kill()
		self.process_collection.clear()


	def invoke_master(self):
		return self.invoke(
			script = "master_main.py",
			arguments = [ "--address", self.master_address, "--port", str(self.master_port), "--database", self.database_uri ],
			workspace = os.path.join(self.temporary_directory, "master"),
		)


	def invoke_worker(self, worker_identifier):
		return self.invoke(
			script = "worker_main.py",
			arguments = [ "--identifier", worker_identifier, "--master-uri", "ws://%s:%s" % (self.master_address, self.master_port) ],
			workspace = os.path.join(self.temporary_directory, worker_identifier),
		)


	def invoke_service(self):
		return self.invoke(
			script = "service_main.py",
			arguments = [ "--address", self.service_address, "--port", str(self.service_port), "--database", self.database_uri ],
			workspace = os.path.join(self.temporary_directory, "master"),
		)


	def invoke_website(self):
		return self.invoke(
			script = "website_main.py",
			arguments = [ "--address", self.website_address, "--port", str(self.website_port) ],
			workspace = os.path.join(self.temporary_directory, "website"),
		)


	def invoke(self, script, arguments, workspace):
		script_root = os.path.dirname(os.path.realpath(__file__))
		command = [ sys.executable, os.path.join(script_root, script) ] + arguments

		os.makedirs(workspace, exist_ok = True)

		process = subprocess.Popen(
			command,
			cwd = workspace,
			stdout = subprocess.PIPE,
			stderr = subprocess.PIPE,
			creationflags = subprocess_flags,
		)

		self.process_collection.append(process)

		time.sleep(1) # Wait for initialization

		return process


	def create_database_client(self):
		if self.database_uri == "json":
			return json_database_client.JsonDatabaseClient(os.path.join(self.temporary_directory, "master"))
		if self.database_uri.startswith("mongodb://"):
			return mongo_database_client.MongoDatabaseClient(pymongo.MongoClient(self.database_uri).get_database())
		raise ValueError("Unsupported database uri '%s'" % self.database_uri)


	def instantiate_providers(self):
		database_client_instance = self.create_database_client()
		file_storage_instance = file_storage.FileStorage(os.path.join(self.temporary_directory, "master"))

		return {
			"build": build_provider.BuildProvider(database_client_instance, file_storage_instance),
			"job": job_provider.JobProvider(database_client_instance),
			"task": task_provider.TaskProvider(database_client_instance),
			"worker": worker_provider.WorkerProvider(database_client_instance),
		}

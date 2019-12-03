# pylint: disable = no-self-use, unused-argument


class WorkerRemoteMock:
	""" Mock a remote worker process to execute commands """


	def __init__(self, worker_identifier):
		self.worker_identifier = worker_identifier
		self.executors = []


	def execute_command(self, command, parameters): # pylint: disable = too-many-return-statements
		if command == "authenticate":
			return self._authenticate()
		if command == "list":
			return self._list_runs()
		if command == "execute":
			return self._execute(**parameters)
		if command == "clean":
			return self._clean(**parameters)
		if command == "abort":
			return self._abort(**parameters)
		if command == "status":
			return self._retrieve_status(**parameters)
		if command == "request":
			return self._retrieve_request(**parameters)
		if command == "log":
			return self._retrieve_log(**parameters)
		if command == "results":
			return self._retrieve_results(**parameters)
		if command == "shutdown":
			return self._request_shutdown()
		raise ValueError("Unknown command '%s'" % command)


	def find_executor(self, run_identifier):
		for executor in self.executors:
			if executor["run_identifier"] == run_identifier:
				return executor
		raise KeyError("Executor not found for %s" % run_identifier)


	def _authenticate(self):
		return { "identifier": self.worker_identifier }


	def _list_runs(self):
		all_runs = []
		for executor in self.executors:
			all_runs.append({ "job_identifier": executor["job_identifier"], "run_identifier": executor["run_identifier"] })
		return all_runs


	def _execute(self, job_identifier, run_identifier, job, parameters):
		executor = {
			"job_identifier": job_identifier,
			"run_identifier": run_identifier,

			"request": {
				"job_identifier": job_identifier,
				"run_identifier": run_identifier,
				"job": job,
				"parameters": parameters,
			},

			"status": {
				"job_identifier": job_identifier,
				"run_identifier": run_identifier,
				"status": "running",
				"steps": [
					{ "index": 0, "name": "first", "status": "pending" },
					{ "index": 1, "name": "second", "status": "pending" },
					{ "index": 2, "name": "third", "status": "pending" },
				],
			},
		}

		self.executors.append(executor)


	def _clean(self, job_identifier, run_identifier):
		executor = self.find_executor(run_identifier)
		if executor["status"]["status"] == "running":
			raise RuntimeError("Executor is still running for run %s" % run_identifier)
		self.executors.remove(executor)


	def _abort(self, job_identifier, run_identifier):
		executor = self.find_executor(run_identifier)
		executor["status"]["status"] = "aborted"


	def _retrieve_status(self, job_identifier, run_identifier):
		executor = self.find_executor(run_identifier)
		return executor["status"]


	def _retrieve_request(self, job_identifier, run_identifier):
		executor = self.find_executor(run_identifier)
		return executor["request"]


	def _retrieve_log(self, job_identifier, run_identifier, step_index, step_name):
		return ""


	def _retrieve_results(self, job_identifier, run_identifier):
		return {}


	def _request_shutdown(self):
		pass

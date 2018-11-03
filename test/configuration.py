service_url = "http://localhost:5100"


def configure():
	workers = _configure_workers()
	jobs = _configure_jobs()

	return { "jobs": jobs, "workers": workers }


def _configure_jobs():
	return [
		test_success(),
		test_failure(),
		test_exception(),
		test_controller_success(),
		test_controller_failure(),
	]


def test_success():
	return {
		"identifier": "test_success",
		"description": "Test job which succeeds.",
		"workspace": "test_project",

		"properties": {
			"project": "test_project",
			"is_controller": False,
		},

		"parameters": [],

		"steps": [
			{ "name": "hello", "command": [ "{environment[python3_executable]}", "-c", "pass" ] },
		],
	}


def test_failure():
	return {
		"identifier": "test_failure",
		"description": "Test job with a failing step.",
		"workspace": "test_project",

		"properties": {
			"project": "test_project",
			"is_controller": False,
		},

		"parameters": [],

		"steps": [
			{ "name": "fail", "command": [ "{environment[python3_executable]}", "-c", "raise RuntimeError" ] },
		],
	}


def test_exception():
	return {
		"identifier": "test_exception",
		"description": "Test job with mistakes in its definition.",
		"workspace": "test_project",

		"properties": {
			"project": "test_project",
			"is_controller": False,
		},

		"parameters": [],

		"steps": [
			{ "name": "exception", "command": [ "{environment[python3_executable]}", "-c", "print('{undefined}')" ] },
		],
	}


def test_controller_success():
	controller_script = [ "{environment[python3_executable]}", "{environment[script_root]}/controller_main.py" ]
	controller_script += [ "--service-url", service_url, "--results", "{result_file_path}" ]

	return {
		"identifier": "test_controller_success",
		"description": "Trigger all test jobs.",
		"workspace": "test_project",

		"properties": {
			"project": "test_project",
			"is_controller": True,
		},

		"parameters": [],

		"steps": [
			{ "name": "trigger", "command": controller_script + [ "trigger", "test_success" ] },
			{ "name": "trigger", "command": controller_script + [ "trigger", "test_success" ] },
			{ "name": "wait", "command": controller_script + [ "wait" ] },
		],
	}


def test_controller_failure():
	controller_script = [ "{environment[python3_executable]}", "{environment[script_root]}/controller_main.py" ]
	controller_script += [ "--service-url", service_url, "--results", "{result_file_path}" ]

	return {
		"identifier": "test_controller_failure",
		"description": "Trigger all test jobs.",
		"workspace": "test_project",

		"properties": {
			"project": "test_project",
			"is_controller": True,
		},

		"parameters": [],

		"steps": [
			{ "name": "trigger", "command": controller_script + [ "trigger", "test_success" ] },
			{ "name": "trigger", "command": controller_script + [ "trigger", "test_failure" ] },
			{ "name": "wait", "command": controller_script + [ "wait" ] },
		],
	}


def _configure_workers():
	return [
		{
			"identifier": "controller",
			"description": "Test build controller",
			"properties": {
				"project": [ "test_project" ],
				"is_controller": True,
				"executor_limit": 100,
			},
		},
		{
			"identifier": "worker_01",
			"description": "Test build worker",
			"properties": {
				"project": [ "test_project" ],
				"is_controller": False,
				"executor_limit": 1,
			},
		},
		{
			"identifier": "worker_02",
			"description": "Test build worker",
			"properties": {
				"project": [ "test_project" ],
				"is_controller": False,
				"executor_limit": 1,
			},
		},
	]


def select_worker(job, all_workers):

	def are_compatible(job, worker):
		return (job["properties"]["project"] in worker["properties"]["project"]
			and job["properties"]["is_controller"] == worker["properties"]["is_controller"])

	def is_available(worker_data, worker_instance):
		return (not worker_instance.should_shutdown
			and are_compatible(job, worker_data)
			and len(worker_instance.executors) < worker_data["properties"]["executor_limit"])

	return next((instance for (data, instance) in all_workers if is_available(data, instance)), None)

def configure():
	jobs = configure_jobs()

	return { "jobs": jobs }


def configure_jobs():
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
	controller_script += [ "--service-url", "{environment[build_service_url]}", ]
	controller_script += [ "--authentication", "{environment[build_worker_authentication]}" ]
	controller_script += [ "--results", "{result_file_path}" ]

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
	controller_script += [ "--service-url", "{environment[build_service_url]}", ]
	controller_script += [ "--authentication", "{environment[build_worker_authentication]}" ]
	controller_script += [ "--results", "{result_file_path}" ]

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

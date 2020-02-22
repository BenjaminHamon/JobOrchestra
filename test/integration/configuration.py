def configure():
	return {
		"projects": configure_projects(),
		"jobs": configure_jobs(),
		"schedules": configure_schedules(),
	}


def configure_projects():
	return [
		{ "identifier": "examples", "services": {} },
	]


def configure_jobs():
	return [
		success(),
		failure(),
		exception(),
		controller_success(),
		controller_failure(),
	]


def configure_schedules():
	return [
		{
			"identifier": "example_success_nightly",
			"project": "examples",
			"job": "examples_success",

			"parameters": [],

			"expression": "0 0 * * *",
		}
	]


def success():
	return {
		"identifier": "examples_success",
		"description": "Test job which succeeds.",
		"project": "examples",
		"workspace": "examples",

		"properties": {
			"is_controller": False,
		},

		"parameters": [],

		"steps": [
			{ "name": "hello", "command": [ "{environment[python3_executable]}", "-c", "pass" ] },
		],
	}


def failure():
	return {
		"identifier": "examples_failure",
		"description": "Test job with a failing step.",
		"project": "examples",
		"workspace": "examples",

		"properties": {
			"is_controller": False,
		},

		"parameters": [],

		"steps": [
			{ "name": "fail", "command": [ "{environment[python3_executable]}", "-c", "raise RuntimeError" ] },
		],
	}


def exception():
	return {
		"identifier": "examples_exception",
		"description": "Test job with mistakes in its definition.",
		"project": "examples",
		"workspace": "examples",

		"properties": {
			"is_controller": False,
		},

		"parameters": [],

		"steps": [
			{ "name": "exception", "command": [ "{environment[python3_executable]}", "-c", "print('{undefined}')" ] },
		],
	}


def controller_success():
	controller_script = [ "{environment[python3_executable]}", "{environment[script_root]}/controller_main.py" ]
	controller_script += [ "--service-url", "{environment[orchestra_service_url]}", ]
	controller_script += [ "--authentication", "{environment[orchestra_worker_authentication]}" ]
	controller_script += [ "--results", "{result_file_path}" ]

	return {
		"identifier": "examples_controller_success",
		"description": "Trigger all test jobs.",
		"project": "examples",
		"workspace": "examples",

		"properties": {
			"is_controller": True,
		},

		"parameters": [],

		"steps": [
			{ "name": "trigger", "command": controller_script + [ "trigger", "examples", "examples_success" ] },
			{ "name": "trigger", "command": controller_script + [ "trigger", "examples", "examples_success" ] },
			{ "name": "wait", "command": controller_script + [ "wait" ] },
		],
	}


def controller_failure():
	controller_script = [ "{environment[python3_executable]}", "{environment[script_root]}/controller_main.py" ]
	controller_script += [ "--service-url", "{environment[orchestra_service_url]}", ]
	controller_script += [ "--authentication", "{environment[orchestra_worker_authentication]}" ]
	controller_script += [ "--results", "{result_file_path}" ]

	return {
		"identifier": "examples_controller_failure",
		"description": "Trigger all test jobs.",
		"project": "examples",
		"workspace": "examples",

		"properties": {
			"is_controller": True,
		},

		"parameters": [],

		"steps": [
			{ "name": "trigger", "command": controller_script + [ "trigger", "examples", "examples_success" ] },
			{ "name": "trigger", "command": controller_script + [ "trigger", "examples", "examples_failure" ] },
			{ "name": "wait", "command": controller_script + [ "wait" ] },
		],
	}

def configure():
	example_project = {
		"identifier": "examples",
		"display_name": "Examples",
		"jobs": configure_jobs(),
		"schedules": configure_schedules(),
		"services": {},
	}

	return {
		"projects": [
			example_project,
		],
	}


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
			"identifier": "success_nightly",
			"job": "success",

			"parameters": [],

			"expression": "0 0 * * *",
		}
	]


def success():
	return {
		"identifier": "success",
		"description": "Test job which succeeds.",
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
		"identifier": "failure",
		"description": "Test job with a failing step.",
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
		"identifier": "exception",
		"description": "Test job with mistakes in its definition.",
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
		"identifier": "controller_success",
		"description": "Trigger all test jobs.",
		"workspace": "examples",

		"properties": {
			"is_controller": True,
		},

		"parameters": [],

		"steps": [
			{ "name": "trigger", "command": controller_script + [ "trigger", "examples", "success" ] },
			{ "name": "trigger", "command": controller_script + [ "trigger", "examples", "success" ] },
			{ "name": "wait", "command": controller_script + [ "wait" ] },
		],
	}


def controller_failure():
	controller_script = [ "{environment[python3_executable]}", "{environment[script_root]}/controller_main.py" ]
	controller_script += [ "--service-url", "{environment[orchestra_service_url]}", ]
	controller_script += [ "--authentication", "{environment[orchestra_worker_authentication]}" ]
	controller_script += [ "--results", "{result_file_path}" ]

	return {
		"identifier": "controller_failure",
		"description": "Trigger all test jobs.",
		"workspace": "examples",

		"properties": {
			"is_controller": True,
		},

		"parameters": [],

		"steps": [
			{ "name": "trigger", "command": controller_script + [ "trigger", "examples", "success" ] },
			{ "name": "trigger", "command": controller_script + [ "trigger", "examples", "failure" ] },
			{ "name": "wait", "command": controller_script + [ "wait" ] },
		],
	}

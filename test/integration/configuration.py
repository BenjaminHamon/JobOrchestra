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
		sleep(),
		failure(),
		exception(),
		controller_success(),
		controller_failure(),
	]


def configure_schedules():
	return [
		{
			"identifier": "success_nightly",
			"display_name": "Success Nightly",
			"job": "success",

			"parameters": {},

			"expression": "0 0 * * *",
		}
	]


def success():
	return {
		"identifier": "success",
		"display_name": "Success",
		"description": "Test job which succeeds.",

		"properties": {
			"is_controller": False,
		},

		"parameters": [],

		"steps": [
			{ "name": "hello", "command": [ "{environment[python3_executable]}", "-c", "pass" ] },
		],
	}


def sleep():
	return {
		"identifier": "sleep",
		"display_name": "Sleep",
		"description": "Test job which succeeds after several seconds.",

		"properties": {
			"is_controller": False,
		},

		"parameters": [],

		"steps": [
			{ "name": "hello", "command": [ "{environment[python3_executable]}", "-c", "import time; time.sleep(5)" ] },
		],
	}


def failure():
	return {
		"identifier": "failure",
		"display_name": "Failure",
		"description": "Test job with a failing step.",

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
		"display_name": "Exception",
		"description": "Test job with mistakes in its definition.",

		"properties": {
			"is_controller": False,
		},

		"parameters": [],

		"steps": [
			{ "name": "exception", "command": [ "{environment[python3_executable]}", "-c", "print('{undefined}')" ] },
		],
	}


def controller_success():
	controller_entry_point = [ "{environment[python3_executable]}", "{environment[script_root]}/controller_main.py" ]
	controller_entry_point += [ "--service-url", "{environment[orchestra_service_url]}", ]
	controller_entry_point += [ "--authentication", "{environment[orchestra_worker_authentication]}" ]
	controller_entry_point += [ "--results", "{result_file_path}" ]

	trigger_source_parameters = [ "--source-project", "{project_identifier}", "--source-run", "{run_identifier}" ]

	return {
		"identifier": "controller_success",
		"display_name": "Controller Success",
		"description": "Trigger all test jobs.",

		"properties": {
			"is_controller": True,
		},

		"parameters": [],

		"steps": [
			{ "name": "trigger", "command": controller_entry_point + [ "trigger", "--project", "examples", "--job", "success" ] + trigger_source_parameters },
			{ "name": "trigger", "command": controller_entry_point + [ "trigger", "--project", "examples", "--job", "success" ] + trigger_source_parameters },
			{ "name": "wait", "command": controller_entry_point + [ "wait" ] },
		],
	}


def controller_failure():
	controller_entry_point = [ "{environment[python3_executable]}", "{environment[script_root]}/controller_main.py" ]
	controller_entry_point += [ "--service-url", "{environment[orchestra_service_url]}", ]
	controller_entry_point += [ "--authentication", "{environment[orchestra_worker_authentication]}" ]
	controller_entry_point += [ "--results", "{result_file_path}" ]

	trigger_source_parameters = [ "--source-project", "{project_identifier}", "--source-run", "{run_identifier}" ]

	return {
		"identifier": "controller_failure",
		"display_name": "Controller Failure",
		"description": "Trigger all test jobs.",

		"properties": {
			"is_controller": True,
		},

		"parameters": [],

		"steps": [
			{ "name": "trigger", "command": controller_entry_point + [ "trigger", "--project", "examples", "--job", "success" ] + trigger_source_parameters },
			{ "name": "trigger", "command": controller_entry_point + [ "trigger", "--project", "examples", "--job", "failure" ] + trigger_source_parameters },
			{ "name": "wait", "command": controller_entry_point + [ "wait" ] },
		],
	}

import flask


def get_build_collection():
	return flask.jsonify(flask.current_app.build_provider.get_all())


def get_build(build_identifier):
	return flask.jsonify(flask.current_app.build_provider.get(build_identifier))


def get_build_step_collection(build_identifier):
	return flask.jsonify(flask.current_app.build_provider.get_all_steps(build_identifier))


def get_build_step(build_identifier, step_index):
	return flask.jsonify(flask.current_app.build_provider.get_step(build_identifier, step_index))


def get_build_step_log(build_identifier, step_index):
	log_text = flask.current_app.build_provider.get_step_log(build_identifier, step_index)
	return flask.Response(log_text, mimetype = "text/plain")


def get_build_results(build_identifier):
	return flask.jsonify(flask.current_app.build_provider.get_results(build_identifier))


def abort_build(build_identifier):
	task = flask.current_app.task_provider.create("abort_build", { "build_identifier": build_identifier })
	return flask.jsonify({ "build_identifier": build_identifier, "task_identifier": task["identifier"] })

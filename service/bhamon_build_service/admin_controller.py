import flask


def reload():
	task = flask.current_app.task_provider.create("reload_configuration", {})
	return flask.jsonify({ "task_identifier": task["identifier"] })

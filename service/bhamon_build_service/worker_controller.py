import flask


def get_worker_collection():
	return flask.jsonify(flask.current_app.worker_provider.get_all())


def get_worker(worker_identifier):
	return flask.jsonify(flask.current_app.worker_provider.get(worker_identifier))


def stop_worker(worker_identifier):
	task = flask.current_app.task_provider.create("stop_worker", { "worker_identifier": worker_identifier })
	return flask.jsonify({ "worker_identifier": worker_identifier, "task_identifier": task["identifier"] })


def enable_worker(worker_identifier):
	flask.current_app.worker_provider.update_status(worker_identifier, is_enabled = True)
	return flask.jsonify({})


def disable_worker(worker_identifier):
	flask.current_app.worker_provider.update_status(worker_identifier, is_enabled = False)
	return flask.jsonify({})

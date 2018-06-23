import asyncio
import logging

import bhamon_build_master.supervisor as supervisor
import bhamon_build_master.task_processor as task_processor


logger = logging.getLogger("Master")


def run(host, port, configuration, database, data_providers):
	logger.info("Starting build master")

	configuration.reload()
	supervisor_instance = supervisor.Supervisor(host, port, configuration, database)
	task_processor_instance = task_processor.TaskProcessor(data_providers["task"])

	task_processor_instance.register_handler("trigger_build", 100, lambda parameters: _trigger_build(parameters, supervisor_instance))

	coroutine_set = asyncio.wait([ supervisor_instance.run_server(), task_processor_instance.run() ])
	asyncio.get_event_loop().run_until_complete(coroutine_set)


def _trigger_build(parameters, supervisor_instance):
	was_triggered = supervisor_instance.trigger_build(parameters["build_identifier"])
	return "succeeded" if was_triggered else "pending"

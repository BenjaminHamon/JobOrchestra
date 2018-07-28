import asyncio
import logging

import bhamon_build_master.supervisor as supervisor
import bhamon_build_master.task_processor as task_processor


logger = logging.getLogger("Master")


def run(host, port, configuration, data_providers):
	logger.info("Starting build master")

	configuration.reload()
	supervisor_instance = supervisor.Supervisor(host, port, configuration, data_providers["worker"], data_providers["build"])
	task_processor_instance = task_processor.TaskProcessor(data_providers["task"])

	task_processor_instance.register_handler("stop_worker", 50,
		lambda parameters: _stop_worker(supervisor_instance, **parameters))
	task_processor_instance.register_handler("abort_build", 90,
		lambda parameters: _abort_build(supervisor_instance, **parameters))
	task_processor_instance.register_handler("trigger_build", 100,
		lambda parameters: _trigger_build(supervisor_instance, **parameters),
		lambda parameters: _cancel_build(data_providers["build"], **parameters))

	main_future = asyncio.gather(supervisor_instance.run_server(), task_processor_instance.run())
	asyncio.get_event_loop().run_until_complete(main_future)


def _stop_worker(supervisor_instance, worker_identifier):
	was_stopped = supervisor_instance.stop_worker(worker_identifier)
	return "succeeded" if was_stopped else "failed"


def _trigger_build(supervisor_instance, build_identifier):
	was_triggered = supervisor_instance.trigger_build(build_identifier)
	return "succeeded" if was_triggered else "pending"


def _cancel_build(build_provider, build_identifier):
	build = build_provider.get(build_identifier)
	if build["status"] == "pending":
		build_provider.update(build, "cancelled")


def _abort_build(supervisor_instance, build_identifier):
	was_aborted = supervisor_instance.abort_build(build_identifier)
	return "succeeded" if was_aborted else "failed"

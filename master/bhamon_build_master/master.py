import asyncio
import logging

import bhamon_build_master.supervisor as supervisor
import bhamon_build_master.task_processor as task_processor


logger = logging.getLogger("Master")


def run(host, port, configuration_loader, data_providers):
	logger.info("Starting build master")

	supervisor_instance = supervisor.Supervisor(host, port, data_providers["worker"], data_providers["job"], data_providers["build"])
	task_processor_instance = task_processor.TaskProcessor(data_providers["task"])

	task_processor_instance.register_handler("stop_worker", 50,
		lambda parameters: _stop_worker(supervisor_instance, **parameters))
	task_processor_instance.register_handler("abort_build", 90,
		lambda parameters: _abort_build(supervisor_instance, **parameters))
	task_processor_instance.register_handler("trigger_build", 100,
		lambda parameters: _trigger_build(supervisor_instance, **parameters),
		lambda parameters: _cancel_build(data_providers["build"], **parameters))

	_reload_configuration(configuration_loader, data_providers["worker"], data_providers["job"])
	main_future = asyncio.gather(supervisor_instance.run_server(), task_processor_instance.run())
	asyncio.get_event_loop().run_until_complete(main_future)


def _reload_configuration(configuration_loader, worker_provider, job_provider):
	logger.info("Reloading configuration")
	configuration = configuration_loader()

	all_existing_workers = worker_provider.get_all()
	for existing_worker_identifier in all_existing_workers.keys():
		if existing_worker_identifier not in [ worker["identifier"] for worker in configuration["workers"] ]:
			logger.info("Removing worker %s", existing_worker_identifier)
			worker_provider.delete(existing_worker_identifier)
	all_existing_jobs = job_provider.get_all()
	for existing_job_identifier in all_existing_jobs.keys():
		if existing_job_identifier not in [ job["identifier"] for job in configuration["jobs"] ]:
			logger.info("Removing job %s", existing_job_identifier)
			job_provider.delete(existing_job_identifier)

	for worker in configuration["workers"]:
		logger.info("Adding/Updating worker %s", worker["identifier"])
		worker_provider.create_or_update(worker["identifier"], worker["properties"], worker["description"])
	for job in configuration["jobs"]:
		logger.info("Adding/Updating job %s", job["identifier"])
		job_provider.create_or_update(job["identifier"], job["workspace"], job["steps"], job["parameters"], job["properties"], job["workers"], job["description"])


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

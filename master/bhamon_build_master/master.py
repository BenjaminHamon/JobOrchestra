import asyncio
import logging

import bhamon_build_master.scheduler as scheduler
import bhamon_build_master.supervisor as supervisor


logger = logging.getLogger("Master")


def run(host, port, configuration, database):
	logger.info("Starting build master")

	configuration.reload()
	supervisor_instance = supervisor.Supervisor(host, port, database)
	scheduler_instance = scheduler.Scheduler(configuration, database, supervisor_instance)

	coroutine_set = asyncio.wait([ supervisor_instance.run_server(), scheduler_instance.run() ])
	asyncio.get_event_loop().run_until_complete(coroutine_set)

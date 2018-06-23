import asyncio
import logging


logger = logging.getLogger("TaskProcessor")

process_delay_seconds = 5


class TaskProcessor:


	def __init__(self, task_provider):
		self._task_provider = task_provider
		self._handler_collection = {}


	def register_handler(self, task_type, order, handler):
		if task_type in self._handler_collection:
			raise KeyError("[TaskProcessor] An handler is already registered for task type '%s'" % task_type)
		self._handler_collection[task_type] = { "order": order, "handler": handler }


	async def run(self):
		while True:
			all_tasks = self._task_provider.get_all()
			all_tasks = [ task for task in all_tasks.values() if task["status"] == "pending" ]
			all_tasks.sort(key = lambda task: ( - self._handler_collection[task["type"]]["order"], task["creation_date"] ))

			for task in all_tasks:
				logger.info("Processing task %s (Type: %s, Parameters: %s)", task["identifier"], task["type"], task["parameters"])

				try:
					task["status"] = "running"
					self._task_provider.update(task)
					end_status = self._handler_collection[task["type"]]["handler"](task["parameters"])
					task["status"] = end_status
					self._task_provider.update(task)

				except:
					logger.warning("Failed to process task %s", task["identifier"], exc_info = True)
					task["status"] = "exception"
					self._task_provider.update(task)

			await asyncio.sleep(process_delay_seconds)

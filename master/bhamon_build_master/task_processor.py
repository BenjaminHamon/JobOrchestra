import asyncio
import logging


logger = logging.getLogger("TaskProcessor")

process_delay_seconds = 5


class TaskProcessor:


	def __init__(self, task_provider):
		self._task_provider = task_provider
		self._handler_collection = {}


	def register_handler(self, task_type, order, execution_handler, cancellation_handler = None):
		if task_type in self._handler_collection:
			raise KeyError("[TaskProcessor] An handler is already registered for task type '%s'" % task_type)
		self._handler_collection[task_type] = {
			"order": order,
			"execution_handler": execution_handler,
			"cancellation_handler": cancellation_handler,
		}


	async def run(self):
		while True:
			all_tasks = self._task_provider.get_all()
			all_tasks = [ task for task in all_tasks.values() if task["status"] == "pending" ]
			all_tasks.sort(key = self._get_task_order)

			for task in all_tasks:
				logger.info("Processing task %s (Type: %s, Parameters: %s)", task["identifier"], task["type"], task["parameters"])

				try:
					self._task_provider.update(task["identifier"], "running")
					if task["should_cancel"]:
						cancellation_handler = self._handler_collection[task["type"]]["cancellation_handler"]
						if cancellation_handler:
							cancellation_handler(task["parameters"])
						end_status = "cancelled"
					else:
						end_status = self._handler_collection[task["type"]]["execution_handler"](task["parameters"])
					self._task_provider.update(task["identifier"], end_status)

				except:
					logger.warning("Failed to process task %s", task["identifier"], exc_info = True)
					self._task_provider.update(task["identifier"], "exception")

			await asyncio.sleep(process_delay_seconds)


	def _get_task_order(self, task):
		try:
			return (self._handler_collection[task["type"]]["order"], task["creation_date"])
		except KeyError:
			return (99999, task["creation_date"])

import asyncio
import logging


logger = logging.getLogger("TaskProcessor")


class TaskProcessor:


	def __init__(self, task_provider):
		self._task_provider = task_provider
		self._handler_collection = {}
		self.update_interval_seconds = 10


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
			try:
				await asyncio.gather(self.update(), asyncio.sleep(self.update_interval_seconds))
			except asyncio.CancelledError: # pylint: disable = try-except-raise
				raise
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception", exc_info = True)


	async def update(self):
		all_tasks = self._list_pending_tasks()

		for task in all_tasks:
			try:
				self._execute_task(task)
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception while processing task %s", task["identifier"], exc_info = True)
				self._task_provider.update_status(task, status = "exception")


	def _list_pending_tasks(self):

		def get_task_order(task):
			task_handler = self._handler_collection.get(task["type"], { "order": 99999 })
			return (task_handler["order"], task["creation_date"])

		all_tasks = self._task_provider.get_list(status = "pending")
		all_tasks.sort(key = get_task_order)
		return all_tasks


	def _execute_task(self, task):
		logger.debug("Executing task %s (Type: %s, Parameters: %s)", task["identifier"], task["type"], task["parameters"])

		self._task_provider.update_status(task, status = "running")
		if task["should_cancel"]:
			cancellation_handler = self._handler_collection[task["type"]]["cancellation_handler"]
			if cancellation_handler is not None:
				cancellation_handler(task["parameters"])
			end_status = "cancelled"
		else:
			end_status = self._handler_collection[task["type"]]["execution_handler"](task["parameters"])
		self._task_provider.update_status(task, status = end_status)

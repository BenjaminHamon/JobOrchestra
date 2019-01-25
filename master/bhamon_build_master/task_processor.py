import asyncio
import logging
import time


logger = logging.getLogger("TaskProcessor")


class TaskProcessor:


	def __init__(self, task_provider):
		self._task_provider = task_provider
		self._handler_collection = {}
		self._should_shutdown = False
		self.update_interval_seconds = 10
		self._active_asyncio_sleep = None


	def register_handler(self, task_type, order, execution_handler, cancellation_handler = None):
		if task_type in self._handler_collection:
			raise KeyError("[TaskProcessor] An handler is already registered for task type '%s'" % task_type)
		self._handler_collection[task_type] = {
			"order": order,
			"execution_handler": execution_handler,
			"cancellation_handler": cancellation_handler,
		}


	async def run(self):
		while not self._should_shutdown:
			update_start = time.time()
			await self._update()
			update_end = time.time()

			try:
				self._active_asyncio_sleep = asyncio.ensure_future(asyncio.sleep(self.update_interval_seconds - (update_end - update_start)))
				await self._active_asyncio_sleep
				self._active_asyncio_sleep = None
			except asyncio.CancelledError:
				break


	async def _update(self):
		try:
			all_tasks = self._task_provider.get_list()
			all_tasks = [ task for task in all_tasks if task["status"] == "pending" ]
			all_tasks.sort(key = self._get_task_order)

			for task in all_tasks:
				logger.debug("Processing task %s (Type: %s, Parameters: %s)", task["identifier"], task["type"], task["parameters"])

				try:
					self._task_provider.update_status(task, status = "running")
					if task["should_cancel"]:
						cancellation_handler = self._handler_collection[task["type"]]["cancellation_handler"]
						if cancellation_handler:
							cancellation_handler(task["parameters"])
						end_status = "cancelled"
					else:
						end_status = self._handler_collection[task["type"]]["execution_handler"](task["parameters"])
					self._task_provider.update_status(task, status = end_status)

				except:
					logger.error("Failed to process task %s", task["identifier"], exc_info = True)
					self._task_provider.update_status(task, status = "exception")

		except:
			logger.error("TaskProcessor update raised an exception", exc_info = True)


	def shutdown(self):
		self._should_shutdown = True
		if self._active_asyncio_sleep:
			self._active_asyncio_sleep.cancel()


	def _get_task_order(self, task):
		try:
			return (self._handler_collection[task["type"]]["order"], task["creation_date"])
		except KeyError:
			return (99999, task["creation_date"])

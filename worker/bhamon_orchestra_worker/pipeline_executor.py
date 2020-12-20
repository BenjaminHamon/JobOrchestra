import asyncio
import enum
import logging

import requests

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.executor import Executor
from bhamon_orchestra_worker.service_client import ServiceClient
from bhamon_orchestra_worker.worker_storage import WorkerStorage


logger = logging.getLogger("Executor")


class TriggerStatus(enum.Enum):
	Ready = 0
	Wait = 1
	Impossible = 2


class PipelineExecutor(Executor):


	def __init__(self, storage: WorkerStorage, date_time_provider: DateTimeProvider, service_client: ServiceClient) -> None:
		super().__init__(storage, date_time_provider)

		self.service_client = service_client

		self.all_inner_runs = []
		self.state = None

		self.running_update_interval_seconds = 10
		self.aborting_update_interval_seconds = 1
		self.abort_timeout_seconds = 20


	async def initialize(self, environment: dict) -> None:
		await super().initialize(environment)

		for element_definition in self.job_definition["elements"]:
			if element_definition.get("project", None) is None:
				element_definition["project"] = self.project_identifier
			if element_definition.get("after", None) is None:
				element_definition["after"] = []
			if element_definition.get("parameters", None) is None:
				element_definition["parameters"] = {}

		for element_definition in self.job_definition["elements"]:
			self.all_inner_runs.append({
				"identifier": None,
				"project": element_definition["project"],
				"element": element_definition["identifier"],
				"status": "pending",
			})

		self._save_results()


	async def execute_implementation(self) -> None:
		try:
			try:
				await self.run_pipeline()
			finally:
				await asyncio.wait_for(self.abort_pipeline(), self.abort_timeout_seconds)

		finally:
			self.run_logging_handler.stream.write("\n")

		self.run_status = self.compute_status()


	async def run_pipeline(self) -> None:
		self.state = "running"

		while not self.is_completed():
			try:
				await asyncio.gather(self.update(), asyncio.sleep(self.running_update_interval_seconds))
			except requests.ConnectionError:
				logger.warning("(%s) Connection error during update", self.run_identifier, exc_info = True)
				self.run_logger.warning("Connection error during update", exc_info = True)
				await asyncio.sleep(60)

		self.state = "completed"


	async def abort_pipeline(self) -> None:
		self.state = "aborting"

		while not self.is_completed():
			try:
				await asyncio.gather(self.update(), asyncio.sleep(self.aborting_update_interval_seconds))
			except requests.ConnectionError:
				logger.warning("(%s) Connection error during update", self.run_identifier, exc_info = True)
				self.run_logger.warning("Connection error during update", exc_info = True)
				await asyncio.sleep(1)

		self.state = "completed"


	async def update(self) -> None:
		if self.state == "aborting":
			for inner_run in self.all_inner_runs:
				if inner_run["identifier"] is not None:
					self._try_abort_inner_run(inner_run)

		for inner_run in self.all_inner_runs:
			if inner_run["identifier"] is None:
				self._try_trigger_inner_run(inner_run)

		for inner_run in self.all_inner_runs:
			if inner_run["identifier"] is not None:
				self._update_inner_run(inner_run)

		self._save_results()


	def is_completed(self) -> bool:
		return all(inner_run["status"] in [ "succeeded", "failed", "exception", "aborted", "skipped", "cancelled" ] for inner_run in self.all_inner_runs)


	def compute_status(self) -> str:
		if any(inner_run["status"] in [ "pending", "running" ] for inner_run in self.all_inner_runs):
			return "running"
		if any(inner_run["status"] in [ "failed", "exception" ] for inner_run in self.all_inner_runs):
			return "failed"
		if any(inner_run["status"] in [ "cancelled", "aborted" ] for inner_run in self.all_inner_runs):
			return "aborted"
		return "succeeded"


	def _try_trigger_inner_run(self, inner_run: dict) -> None:
		trigger_status = self._can_trigger_inner_run(inner_run)

		if trigger_status == TriggerStatus.Ready:
			self._trigger_inner_run(inner_run)

		if trigger_status == TriggerStatus.Impossible:
			logger.info("(%s) Skipping '%s': trigger conditions cannot be satisfied", self.run_identifier, inner_run["element"])
			inner_run["status"] = "skipped"


	def _can_trigger_inner_run(self, inner_run: dict) -> TriggerStatus:
		element_definition = next(element for element in self.job_definition["elements"] if element["identifier"] == inner_run["element"])

		for after_option in element_definition["after"]:
			predecessor = next(r for r in self.all_inner_runs if r["element"] == after_option["element"])
			if predecessor["status"] not in after_option["status"]:
				if predecessor["status"] in [ "succeeded", "failed", "aborted", "cancelled", "skipped", "exception" ]:
					return TriggerStatus.Impossible
				return TriggerStatus.Wait

		return TriggerStatus.Ready


	def _trigger_inner_run(self, inner_run: dict) -> None:
		logger.info("(%s) Triggering '%s'", self.run_identifier, inner_run["element"])
		self.run_logger.info("Triggering '%s'", inner_run["element"])

		element_definition = next(element for element in self.job_definition["elements"] if element["identifier"] == inner_run["element"])
		source = { "type": "run", "project": self.project_identifier, "identifier": self.run_identifier }

		parameters = { key: self.format_value(value) for key, value in element_definition["parameters"].items() }
		trigger_response = self.service_client.trigger_job(element_definition["project"], element_definition["job"], parameters, source)
		inner_run["identifier"] = trigger_response["run_identifier"]

		logger.info("(%s) Triggered '%s' as run '%s'", self.run_identifier, inner_run["element"], inner_run["identifier"])
		self.run_logger.info("Triggered '%s' as run '%s'", inner_run["element"], inner_run["identifier"])


	def _try_abort_inner_run(self, inner_run: dict) -> None:
		if inner_run["status"] in [ "pending", "running" ]:
			run_record = self.service_client.get_run(inner_run["project"], inner_run["identifier"])
			inner_run["status"] = run_record["status"]

			if inner_run["status"] == "pending" and not run_record["should_cancel"]:
				logger.info("(%s) Cancelling '%s'", self.run_identifier, inner_run["element"])
				self.service_client.cancel_run(inner_run["project"], inner_run["identifier"])

			if inner_run["status"] == "running" and not run_record["should_abort"]:
				logger.info("(%s) Aborting '%s'", self.run_identifier, inner_run["element"])
				self.service_client.abort_run(inner_run["project"], inner_run["identifier"])


	def _update_inner_run(self, inner_run: dict) -> None:
		logger.debug("(%s) Updating '%s'", self.run_identifier, inner_run["element"])
		self.run_logger.debug("Updating '%s'", inner_run["element"])

		last_status = inner_run["status"]
		if last_status in [ "unknown", "pending", "running" ]:
			run_record = self.service_client.get_run(inner_run["project"], inner_run["identifier"])
			inner_run["status"] = run_record["status"]

		if last_status in [ "unknown", "pending" ] and inner_run["status"] == "running":
			logger.info("(%s) Started '%s' as run '%s'", self.run_identifier, inner_run["element"], inner_run["identifier"])
			self.run_logger.info("Started '%s' as run '%s'", inner_run["element"], inner_run["identifier"])
		if last_status in [ "unknown", "pending", "running" ] and inner_run["status"] not in [ "pending", "running" ]:
			logger.info("(%s) Completed '%s' as run '%s' with status '%s'", self.run_identifier, inner_run["element"], inner_run["identifier"], inner_run["status"])
			self.run_logger.info("Completed '%s' as run '%s' with status '%s'", inner_run["element"], inner_run["identifier"], inner_run["status"])


	def _save_results(self) -> None:
		results = self._storage.load_results(self.run_identifier)
		results["pipeline"] = { "elements": self.job_definition["elements"], "inner_runs": self.all_inner_runs }
		self._storage.save_results(self.run_identifier, results)

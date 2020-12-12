import abc


class ServiceClient(abc.ABC):
	""" Base class of a communication client for the worker with the Orchestra service """


	@abc.abstractmethod
	def get_run(self, project_identifier: str, run_identifier: str) -> dict:
		pass


	@abc.abstractmethod
	def trigger_job(self, project_identifier: str, job_identifier: str, parameters: dict, source: dict) -> dict:
		pass

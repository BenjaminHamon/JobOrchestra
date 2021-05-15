import abc
from typing import List, Optional


class RevisionControlClient(abc.ABC):


	@abc.abstractmethod
	def get_repository(self, repository: str) -> dict:
		""" Return a repository """


	@abc.abstractmethod
	def get_branch_list(self, repository: str) -> dict:
		""" Return the list of branches from a repository """


	@abc.abstractmethod
	def get_revision_list(self, repository: str, reference: Optional[str] = None, limit: Optional[int] = None) -> List[dict]:
		""" Return a list of revisions from a repository and an optional starting reference """


	@abc.abstractmethod
	def get_revision(self, repository: str, reference: str) -> dict:
		""" Return a single revision from a repository and a reference """


	@abc.abstractmethod
	def get_reference_url(self, repository: str, reference: str) -> str:
		""" Return the web url for a reference """

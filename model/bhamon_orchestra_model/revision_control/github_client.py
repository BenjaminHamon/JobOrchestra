import datetime
import logging
from typing import Any, List, Optional

import requests

from bhamon_orchestra_model.revision_control.revision_control_client import RevisionControlClient
from bhamon_orchestra_model.serialization.serializer import Serializer


logger = logging.getLogger("GitHub")


class GitHubClient(RevisionControlClient):


	def __init__(self, serializer: Serializer, access_token: Optional[str] = None) -> None:
		self._serializer = serializer
		self.access_token = access_token

		self.website_url = "https://github.com"
		self.service_url = "https://api.github.com"
		self.timeout = datetime.timedelta(seconds = 30)


	def get_repository(self, repository: str) -> dict:
		route = "/repos/" + repository
		response = self.send_request("GET", route)

		return {
			"identifier": response["full_name"],
			"owner": response["owner"]["login"],
			"name": response["name"],
			"description": response["description"],
			"url": response["html_url"],
			"default_branch": response["default_branch"],
		}


	def get_branch_list(self, repository: str) -> dict:
		route = "/repos/" + repository + "/branches"
		response = self.send_request("GET", route)
		return [ item["name"] for item in response ]


	def get_revision_list(self, repository: str, reference: Optional[str] = None, limit: Optional[int] = None) -> List[dict]:
		route = "/repos/" + repository + "/commits"
		parameters = { "sha": reference, "per_page": limit }
		parameters = { key: value for key, value in parameters.items() if value is not None }
		response = self.send_request("GET", route, parameters)

		revision_list = []
		for item in response:
			revision_list.append({
				"identifier": item["sha"],
				"identifier_short": item["sha"][:10],
				"author": item["commit"]["author"]["name"],
				"date": item["commit"]["committer"]["date"],
				"description": item["commit"]["message"],
				"url": item["html_url"],
			})

		return revision_list


	def get_revision(self, repository: str, reference: str) -> dict:
		route = "/repos/" + repository + "/commits/" + reference
		response = self.send_request("GET", route)

		return {
			"identifier": response["sha"],
			"identifier_short": response["sha"][:10],
			"author": response["commit"]["author"]["name"],
			"date": response["commit"]["committer"]["date"],
			"description": response["commit"]["message"],
			"url": response["html_url"],
		}


	def get_reference_url(self, repository: str, reference: str) -> str:
		return self.website_url + "/" + repository + "/commit/" + reference


	def send_request(self, method: str, route: str, parameters: Optional[dict] = None, data: Optional[Any] = None) -> Optional[Any]:
		logger.debug("%s %s", method, self.service_url + route)

		headers = { "Accept": self._serializer.get_content_type() }
		if self.access_token is not None:
			headers["Authorization"] = "token %s" % self.access_token

		serialized_data = None
		if data is not None:
			headers["Content-Type"] = self._serializer.get_content_type()
			serialized_data = self._serializer.serialize_to_string(data)

		response = requests.request(method, self.service_url + route,
			headers = headers, params = parameters, data = serialized_data, timeout = self.timeout.total_seconds())

		response.raise_for_status()

		if response.headers["Content-Type"].split(";")[0] == self._serializer.get_content_type():
			return self._serializer.deserialize_from_string(response.text)

		raise RuntimeError("Unsupported response content-type '%s'" % response.headers["Content-Type"])

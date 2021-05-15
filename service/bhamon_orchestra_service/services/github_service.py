import datetime
import logging
from typing import Any, Optional

import requests

from bhamon_orchestra_model.serialization.serializer import Serializer
from bhamon_orchestra_service.services.service import Service


logger = logging.getLogger("GitHub")


class GitHubService(Service):


	def __init__(self, serializer: Serializer, access_token: Optional[str] = None) -> None:
		self._serializer = serializer
		self.access_token = access_token

		self.identifier = "github"
		self.display_name = "GitHub"
		self.website_url = "https://github.com"
		self.service_url = "https://api.github.com"
		self.status_url = "https://www.githubstatus.com"


	def get_definition(self) -> dict:
		return {
			"identifier": self.identifier,
			"display_name": self.display_name,
			"website_url": self.website_url,
			"service_url": self.service_url,
			"status_url": self.status_url,
		}


	def get_status(self) -> dict:
		try:
			rate_limit = self.get_api_rate_limit()

			return {
				"status": "available",
				"rate_limit": rate_limit,
			}

		except requests.HTTPError as exception:
			return {
				"status": "unavailable",
				"status_code": exception.response.status_code,
				"status_message": exception.response.reason,
			}


	def get_api_rate_limit(self) -> dict:
		rate_limit_raw = self.send_request("GET", "/rate_limit")

		rate_limit = {
			"status": "unknown",
			"limit": rate_limit_raw["resources"]["core"]["limit"],
			"remaining": rate_limit_raw["resources"]["core"]["remaining"],
			"reset": datetime.datetime.utcfromtimestamp(rate_limit_raw["resources"]["core"]["reset"]).isoformat() + "Z",
			"raw_response": rate_limit_raw,
		}

		if rate_limit["remaining"] < rate_limit["limit"] * 0.1:
			rate_limit["status"] = "critical"
		elif rate_limit["remaining"] < rate_limit["limit"] * 0.5:
			rate_limit["status"] = "warning"
		else:
			rate_limit["status"] = "okay"

		return rate_limit


	def send_request(self, method: str, route: str, parameters: Optional[dict] = None, data: Optional[Any] = None) -> Optional[Any]:
		logger.debug("%s %s", method, self.service_url + route)

		headers = { "Accept": self._serializer.get_content_type() }
		if self.access_token is not None:
			headers["Authorization"] = "token %s" % self.access_token

		serialized_data = None
		if data is not None:
			headers["Content-Type"] = self._serializer.get_content_type()
			serialized_data = self._serializer.serialize_to_string(data)

		response = requests.request(method, self.service_url + route, headers = headers, params = parameters, data = serialized_data)

		response.raise_for_status()

		if response.headers["Content-Type"].split(";")[0] == self._serializer.get_content_type():
			return self._serializer.deserialize_from_string(response.text)

		raise RuntimeError("Unsupported response content-type '%s'" % response.headers["Content-Type"])

import datetime
import logging

from typing import Any, List, Optional

import requests


logger = logging.getLogger("GitHub")

website_url = "https://github.com"
status_url = "https://www.githubstatus.com"
api_url = "https://api.github.com"


class GitHubClient:


	def __init__(self, access_token: Optional[str] = None) -> None:
		self.access_token = access_token


	def get_service_status(self) -> dict:
		return self.get_api_status()


	def get_api_status(self) -> dict:
		result = {
			"service": "GitHub",
			"website_url": website_url,
			"status_url": status_url,
		}

		try:
			rate_limit = self.get_api_rate_limit()
			result.update({ "status": "available", "rate_limit": rate_limit })
		except requests.HTTPError as exception:
			result.update({
				"status": "unavailable",
				"status_code": exception.response.status_code,
				"status_message": exception.response.reason,
			})

		return result


	def get_api_rate_limit(self) -> dict:
		rate_limit_raw = self.send_get_request("/rate_limit")

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


	def get_repository(self, repository: str) -> dict: # pylint: disable = unused-argument
		route = "/repos/{repository}".format(**locals())
		response = self.send_get_request(route)

		return {
			"identifier": response["full_name"],
			"owner": response["owner"]["login"],
			"name": response["name"],
			"description": response["description"],
			"url": response["html_url"],
			"default_branch": response["default_branch"],
		}


	def get_branch_list(self, repository: str) -> dict: # pylint: disable = unused-argument
		route = "/repos/{repository}/branches".format(**locals())
		response = self.send_get_request(route)
		return [ item["name"] for item in response ]


	def get_revision_list(self, repository: str, branch: Optional[str] = None, limit: Optional[int] = None) -> List[dict]: # pylint: disable = unused-argument
		route = "/repos/{repository}/commits".format(**locals())
		parameters = { "sha": branch, "per_page": limit }
		parameters = { key: value for key, value in parameters.items() if value is not None }
		response = self.send_get_request(route, parameters)

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


	def get_revision(self, repository: str, revision: str) -> dict: # pylint: disable = unused-argument
		route = "/repos/{repository}/commits/{revision}".format(**locals())
		response = self.send_get_request(route)

		return {
			"identifier": response["sha"],
			"identifier_short": response["sha"][:10],
			"author": response["commit"]["author"]["name"],
			"date": response["commit"]["committer"]["date"],
			"description": response["commit"]["message"],
			"url": response["html_url"],
		}


	def get_revision_url(self, repository: str, revision: str) -> str: # pylint: disable = no-self-use, unused-argument
		return website_url + "/{repository}/commit/{revision}".format(**locals())


	def send_get_request(self, route: str, parameters: Optional[dict] = None) -> Any:
		headers = { "Content-Type": "application/json" }
		if self.access_token is not None:
			headers["Authorization"] = "token %s" % self.access_token

		logger.debug("GET %s", api_url + route)
		response = requests.get(api_url + route, headers = headers, params = parameters)
		response.raise_for_status()
		return response.json()

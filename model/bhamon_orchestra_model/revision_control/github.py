import logging

import requests


logger = logging.getLogger("GitHub")

website_url = "https://github.com"
api_url = "https://api.github.com"


class GitHubClient:


	def __init__(self, access_token = None):
		self.access_token = access_token


	def get_repository(self, repository): # pylint: disable = unused-argument
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


	def get_branch_list(self, repository): # pylint: disable = unused-argument
		route = "/repos/{repository}/branches".format(**locals())
		response = self.send_get_request(route)
		return [ item["name"] for item in response ]


	def get_revision_list(self, repository, branch = None, limit = None): # pylint: disable = unused-argument
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


	def get_revision(self, repository, revision): # pylint: disable = unused-argument
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


	def get_revision_url(self, repository, revision): # pylint: disable = no-self-use, unused-argument
		return website_url + "/{repository}/commit/{revision}".format(**locals())


	def send_get_request(self, route, parameters = None):
		headers = { "Content-Type": "application/json" }
		if self.access_token is not None:
			headers["Authorization"] = "token %s" % self.access_token

		logger.debug("GET %s", api_url + route)
		response = requests.get(api_url + route, headers = headers, params = parameters)
		response.raise_for_status()
		return response.json()

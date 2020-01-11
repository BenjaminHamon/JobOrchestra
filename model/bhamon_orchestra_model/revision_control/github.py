import logging

import requests


logger = logging.getLogger("GitHub")


website_url = "https://github.com"
api_url = "https://api.github.com"



class GitHubRepositoryClient:


	def __init__(self, owner, repository, access_token = None):
		self.owner = owner
		self.repository = repository
		self.inner_client = GitHubClient(access_token)


	def get_branch_list(self):
		return self.inner_client.get_branch_list(self.owner, self.repository)


	def get_revision_list(self, branch = None, limit = None):
		return self.inner_client.get_revision_list(self.owner, self.repository, branch = branch, limit = limit)


	def get_revision(self, revision):
		return self.inner_client.get_revision(self.owner, self.repository, revision)


	def get_revision_url(self, revision):
		return self.inner_client.get_revision_url(self.owner, self.repository, revision)



class GitHubClient:


	def __init__(self, access_token = None):
		self.access_token = access_token


	def get_branch_list(self, owner, repository): # pylint: disable = unused-argument
		route = "/repos/{owner}/{repository}/branches".format(**locals())
		response = self.send_get_request(route)
		return [ item["name"] for item in response ]


	def get_revision_list(self, owner, repository, branch = None, limit = None): # pylint: disable = unused-argument
		route = "/repos/{owner}/{repository}/commits".format(**locals())
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


	def get_revision(self, owner, repository, revision): # pylint: disable = unused-argument
		route = "/repos/{owner}/{repository}/commits/{revision}".format(**locals())
		response = self.send_get_request(route)

		return {
			"identifier": response["sha"],
			"identifier_short": response["sha"][:10],
			"author": response["commit"]["author"]["name"],
			"date": response["commit"]["committer"]["date"],
			"description": response["commit"]["message"],
			"url": response["html_url"],
		}


	def get_revision_url(self, owner, repository, revision): # pylint: disable = no-self-use, unused-argument
		return website_url + "/{owner}/{repository}/commit/{revision}".format(**locals())


	def send_get_request(self, route, parameters = None):
		headers = { "Content-Type": "application/json" }
		if self.access_token is not None:
			headers["Authorization"] = "token %s" % self.access_token

		logger.debug("GET %s", api_url + route)
		response = requests.get(api_url + route, headers = headers, params = parameters)
		response.raise_for_status()
		return response.json()

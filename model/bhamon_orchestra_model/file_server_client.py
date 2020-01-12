import requests


class FileServerClient: # pylint: disable = too-few-public-methods


	def __init__(self, name, website_url):
		self.name = name
		self.website_url = website_url


	def get_service_status(self):
		result = {
			"service": self.name,
			"website_url": self.website_url,
		}

		try:
			response = requests.get(self.website_url + "/")
			response.raise_for_status()
			result.update({ "status": "available" })
		except requests.HTTPError as exception:
			result.update({
				"status": "unavailable",
				"status_code": exception.response.status_code,
				"status_message": exception.response.reason,
			})

		return result

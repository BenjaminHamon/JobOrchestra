import datetime

import requests

from bhamon_orchestra_service.services.service import Service


class FileService(Service):


	def __init__(self, identifier: str, display_name: str, website_url: str) -> None:
		self.identifier = identifier
		self.display_name = display_name
		self.website_url = website_url

		self.timeout = datetime.timedelta(seconds = 30)


	def get_definition(self) -> dict:
		return {
			"identifier": self.identifier,
			"display_name": self.display_name,
			"website_url": self.website_url,
		}


	def get_status(self) -> dict:
		try:
			response = requests.get(self.website_url + "/", timeout = self.timeout.total_seconds())
			response.raise_for_status()

			return {
				"status": "available",
			}

		except requests.HTTPError as exception:
			return {
				"status": "unavailable",
				"status_code": exception.response.status_code,
				"status_message": exception.response.reason,
			}

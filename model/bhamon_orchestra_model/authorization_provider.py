import logging

from typing import List


logger = logging.getLogger("AuthorizationProvider")


class AuthorizationProvider:
	""" Expose methods to check if a user is authorized to view a resource or perform an action.

	Authorization is computed based on the user (anonymous or not, enabled or not, their roles)
	and the resource or action they target (defined by an identifier or a route).

	Roles:
	- Administrator: full read-write access to web routes
	- Auditor: full read-only access to web routes
	- Operator: read-write access to web routes by whitelist (all but administration)
	- Viewer: read-only access to web routes by whitelist (all but administration)
	- Worker: connection access to the master, access to web routes for triggering jobs and viewing runs
	"""


	def authorize_request(self, user: dict, method: str, route: str) -> bool:
		""" Check if a user is authorized to perform a web request with the provided method and route """
		if self.is_public_route(method, route):
			return True
		if self.is_active_user(user) and self.is_route_authorized_for_roles(user["roles"], method, route):
			return True
		return False


	def authorize_view(self, user: dict, view: str) -> bool:
		""" Check if a user is authorized to see a set of resources, based on a view identifier

		This is useful when displaying a complex web page with links to resources with varying authorization requirements. """

		if self.is_active_user(user) and self.is_view_authorized_for_roles(user["roles"], view):
			return True
		return False


	def authorize_worker(self, user: dict) -> bool:
		""" Check if a user is authorized to run a worker """
		if self.is_active_user(user) and "Worker" in user["roles"]:
			return True
		return False


	def is_active_user(self, user: dict) -> bool: # pylint: disable = no-self-use
		""" Check if a user is registered and enabled """
		return user is not None and user["is_enabled"]


	def is_public_route(self, method: str, route: str) -> bool: # pylint: disable = no-self-use, too-many-return-statements
		""" Check if a route is public, meaning any user, even anonymous, is authorized to use it """

		if method == "GET" and route == "/":
			return True
		if method == "GET" and route == "/help":
			return True
		if method == "GET" and route in [ "/me/login", "/me/logout" ]:
			return True
		if method == "POST" and route in [ "/me/login", "/me/logout" ]:
			return True
		if method == "GET" and route == "/service_proxy":
			return True
		if method == "GET" and route.startswith("/service_proxy/"):
			return True
		if method == "POST" and route.startswith("/service_proxy/"):
			return True
		if method == "GET" and route.startswith("/static/"):
			return True
		return False


	def is_route_authorized_for_roles(self, user_roles: List[str], method: str, route: str) -> bool: # pylint: disable = too-many-branches, too-many-return-statements
		""" Check if the given set of user roles authorizes using the provided method and route for a web request """

		if "Administrator" in user_roles:
			return True
		if "Auditor" in user_roles and method == "GET":
			return True

		if method == "GET" and route == "/":
			return True
		if method == "GET" and route == "/help":
			return True

		domain = self.get_route_domain(route)

		if domain == "me":
			return True

		if domain in [ "admin", "user" ]:
			if "Administrator" in user_roles:
				return True
			if "Auditor" in user_roles and method == "GET":
				return True

		if method == "GET" and domain in [ "project", "run", "schedule", "task", "worker" ]:
			if "Viewer" in user_roles:
				return True
		if method == "POST" and domain in [ "run", "schedule", "task", "worker" ]:
			if "Operator" in user_roles:
				return True

		if method == "GET" and route == "/run/<run_identifier>":
			if "Worker" in user_roles:
				return True
		if method == "POST" and route == "/project/<project_identifier>/job/<job_identifier>/trigger":
			if "Worker" in user_roles:
				return True

		return False


	def is_view_authorized_for_roles(self, user_roles: List[str], view: str) -> bool: # pylint: disable = no-self-use, too-many-return-statements
		""" Check if the given set of user roles authorizes seeing a set of resources, based on a view identifier """

		if "Administrator" in user_roles:
			return True

		if view in [ "nav-admin" ]:
			if "Administrator" in user_roles:
				return True
			if "Auditor" in user_roles:
				return True
		if view in [ "nav-main" ]:
			if "Auditor" in user_roles:
				return True
			if "Viewer" in user_roles:
				return True

		if view in [ "job-actions", "run-actions", "schedule-actions", "task-actions", "worker-actions" ]:
			if "Operator" in user_roles:
				return True

		return False


	def get_administrator_roles(self) -> List[str]: # pylint: disable = no-self-use
		""" Return the default list of roles for a user with administrator privileges """
		return [ "Administrator" ]


	def get_route_domain(self, route: str) -> str: # pylint: disable = no-self-use
		""" Return the domain from a route, meaning its first element """
		return route.replace("_", "/").split("/")[1]

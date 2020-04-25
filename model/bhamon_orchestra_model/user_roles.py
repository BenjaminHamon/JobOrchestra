""" Implementation of authorization checks for all user roles, used by AuthorizationProvider """

# pylint: disable = no-self-use, unused-argument


class Anonymous:
	""" Automatic role for a user not logged in, with minimal access to web routes (home, help, login, static) """


	def is_route_authorized(self, method: str, route: str) -> bool:
		if method == "GET":
			if route in [ "/", "/help" ]:
				return True
			if route.startswith("/static/"):
				return True

		if method in [ "GET", "POST" ]:
			if route in [ "/me/login", "/me/logout" ]:
				return True

		return False


	def is_view_authorized(self, view: str) -> bool:
		return False



class Default:
	""" Automatic role for any user logged in, with minimal access to web routes (home, help, me, service proxy, static) """


	def is_route_authorized(self, method: str, route: str) -> bool:
		if method == "GET":
			if route in [ "/", "/help", "/me", "/service_proxy" ]:
				return True
			if route.startswith("/static/"):
				return True

		if method in [ "GET", "POST" ]:
			if route.startswith("/me/"):
				return True
			if route.startswith("/service_proxy/"):
				return True

		return False


	def is_view_authorized(self, view: str) -> bool:
		return False



class Administrator:
	""" User role with full read-write access to web routes """


	def is_route_authorized(self, method: str, route: str) -> bool:
		return True


	def is_view_authorized(self, view: str) -> bool:
		return True



class Auditor:
	""" User role with full read access to web routes """


	def is_route_authorized(self, method: str, route: str) -> bool:
		return method == "GET"


	def is_view_authorized(self, view: str) -> bool:
		if view in [ "nav-admin", "nav-main", "user-security" ]:
			return True
		return False



class Operator:
	""" User role with write access to web routes by whitelist (all but administration) """


	def is_route_authorized(self, method: str, route: str) -> bool:
		if method == "POST":
			if route.startswith("/project/<project_identifier>/job/"):
				return True
			if route.startswith("/project/<project_identifier>/run/"):
				return True
			if route.startswith("/project/<project_identifier>/schedule/"):
				return True
			if route.startswith("/worker/"):
				return True

		return False


	def is_view_authorized(self, view: str) -> bool:
		if view in [ "job-actions", "run-actions", "schedule-actions", "worker-actions" ]:
			return True
		return False



class Viewer:
	""" User role with read access to web routes by whitelist (all but administration) """


	def is_route_authorized(self, method: str, route: str) -> bool:
		if method == "GET":
			if route in [ "/project_collection", "/project_count" ]:
				return True
			if route.startswith("/project/"):
				return True
			if route in [ "/user_collection", "/user_count", "/user/<user_identifier>" ]:
				return True
			if route in [ "/worker_collection", "/worker_count" ]:
				return True
			if route.startswith("/worker/"):
				return True

		return False


	def is_view_authorized(self, view: str) -> bool:
		if view in [ "nav-main" ]:
			return True
		return False



class Worker:
	""" User role with connection access to the master, access to web routes for triggering jobs and viewing runs """


	def is_route_authorized(self, method: str, route: str) -> bool:
		if method == "GET" and route == "/project/<project_identifier>/run/<run_identifier>":
			return True
		if method == "POST" and route == "/project/<project_identifier>/job/<job_identifier>/trigger":
			return True
		return False


	def is_view_authorized(self, view: str) -> bool:
		return False

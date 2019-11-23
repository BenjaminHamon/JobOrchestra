import logging


logger = logging.getLogger("AuthorizationProvider")


class AuthorizationProvider:


	def authorize_request(self, user, method, route):
		if self.is_public_route(method, route):
			return True
		if self.is_authorized_user(user) and self.is_authorized_route(user["roles"], method, route):
			return True
		return False


	def authorize_view(self, user, view):
		if self.is_authorized_user(user) and self.is_authorized_view(user["roles"], view):
			return True
		return False


	def authorize_worker(self, user):
		if self.is_authorized_user(user) and "BuildWorker" in user["roles"]:
			return True
		return False


	def get_administrator_roles(self): # pylint: disable = no-self-use
		return [ "Administrator" ]


	def is_authorized_user(self, user): # pylint: disable = no-self-use
		return user is not None and user["is_enabled"]


	def is_public_route(self, method, route): # pylint: disable = no-self-use
		if method == "GET" and route == "/":
			return True
		if method == "GET" and route == "/help":
			return True
		if method == "GET" and route in [ "/me/login", "/me/logout" ]:
			return True
		if method == "POST" and route in [ "/me/login", "/me/logout" ]:
			return True
		if method == "GET" and route.startswith("/static/"):
			return True
		return False


	def is_authorized_route(self, user_roles, method, route): # pylint: disable = too-many-branches, too-many-return-statements
		if "Administrator" in user_roles:
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

		if method == "GET" and domain in [ "build", "job", "task", "worker" ]:
			if "Viewer" in user_roles:
				return True
		if method == "POST" and domain in [ "build", "job", "task", "worker" ]:
			if "Operator" in user_roles:
				return True

		if method == "GET" and route == "/build/<build_identifier>":
			if "BuildWorker" in user_roles:
				return True
		if method == "POST" and route == "/job/<job_identifier>/trigger":
			if "BuildWorker" in user_roles:
				return True

		return False


	def is_authorized_view(self, user_roles, view): # pylint: disable = no-self-use
		if "Administrator" in user_roles:
			return True

		if view in [ "nav-admin" ]:
			if "Administrator" in user_roles:
				return True
		if view in [ "nav-main" ]:
			if "Viewer" in user_roles:
				return True

		if view in [ "build-actions", "job-actions", "task-actions", "worker-actions" ]:
			if "Operator" in user_roles:
				return True

		return False


	def get_route_domain(self, route): # pylint: disable = no-self-use
		return route.replace("_", "/").split("/")[1]

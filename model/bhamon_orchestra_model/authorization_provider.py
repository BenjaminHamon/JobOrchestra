import logging

from typing import List, Optional

import bhamon_orchestra_model.user_roles as user_role_classes


logger = logging.getLogger("AuthorizationProvider")


class AuthorizationProvider:
	""" Expose methods to check if a user is authorized to view a resource or perform an action. """


	def authorize_request(self, user: Optional[dict], method: str, route: str) -> bool:
		""" Check if a user is authorized to perform a web request with the provided method and route """

		user_roles = self.build_user_roles(user)

		for role in user_roles:
			if role.is_route_authorized(method, route):
				return True

		return False


	def authorize_view(self, user: Optional[dict], view: str) -> bool:
		""" Check if a user is authorized to see a set of resources, based on a view identifier

		This is useful when displaying a complex web page with links to resources with varying authorization requirements. """

		user_roles = self.build_user_roles(user)

		for role in user_roles:
			if role.is_view_authorized(view):
				return True

		return False


	def authorize_worker(self, user: Optional[dict]) -> bool: # pylint: disable = no-self-use
		""" Check if a user is authorized to run a worker """
		return user is not None and user["is_enabled"] and "Worker" in user["roles"]


	def build_user_roles(self, user: Optional[dict]) -> List[object]: # pylint: disable = no-self-use
		""" Instantiate user role classes based on a user record """

		if user is None:
			return [ user_role_classes.Anonymous() ]
		if not user["is_enabled"]:
			return [ user_role_classes.Default() ]

		user_roles = [ user_role_classes.Default() ]

		if "Administrator" in user["roles"]:
			user_roles.append(user_role_classes.Administrator())
		if "Auditor" in user["roles"]:
			user_roles.append(user_role_classes.Auditor())
		if "Operator" in user["roles"]:
			user_roles.append(user_role_classes.Operator())
		if "Viewer" in user["roles"]:
			user_roles.append(user_role_classes.Viewer())
		if "Worker" in user["roles"]:
			user_roles.append(user_role_classes.Worker())

		return user_roles


	def get_administrator_roles(self) -> List[str]: # pylint: disable = no-self-use
		""" Return the default list of roles for a user with administrator privileges """
		return [ "Administrator" ]

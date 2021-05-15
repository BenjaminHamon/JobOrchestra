""" Unit tests for AuthenticationProvider """

import datetime
import secrets

from bhamon_orchestra_model.database.memory_database_client import MemoryDatabaseClient
from bhamon_orchestra_model.users.authentication_provider import AuthenticationProvider

from ..fakes.fake_date_time_provider import FakeDateTimeProvider


def test_password_success():
	""" Test password operations succeed in a normal situation """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	provider = AuthenticationProvider(date_time_provider_instance)

	user = "user"
	first_secret = "first"
	second_secret = "second"
	wrong_secret = "wrong"

	assert provider.authenticate_with_password(database_client_instance, user, first_secret) is False
	assert provider.authenticate_with_password(database_client_instance, user, second_secret) is False
	assert provider.authenticate_with_password(database_client_instance, user, wrong_secret) is False

	provider.set_password(database_client_instance, user, first_secret)
	assert provider.authenticate_with_password(database_client_instance, user, first_secret) is True
	assert provider.authenticate_with_password(database_client_instance, user, second_secret) is False
	assert provider.authenticate_with_password(database_client_instance, user, wrong_secret) is False

	provider.set_password(database_client_instance, user, second_secret)
	assert provider.authenticate_with_password(database_client_instance, user, first_secret) is False
	assert provider.authenticate_with_password(database_client_instance, user, second_secret) is True
	assert provider.authenticate_with_password(database_client_instance, user, wrong_secret) is False

	provider.remove_password(database_client_instance, user)
	assert provider.authenticate_with_password(database_client_instance, user, first_secret) is False
	assert provider.authenticate_with_password(database_client_instance, user, second_secret) is False
	assert provider.authenticate_with_password(database_client_instance, user, wrong_secret) is False


def test_token_success():
	""" Test token operations succeed in a normal situation """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	provider = AuthenticationProvider(date_time_provider_instance)

	user = "user"
	wrong_secret = secrets.token_hex(provider.token_size)

	assert provider.count_tokens(database_client_instance, user) == 0
	assert provider.authenticate_with_token(database_client_instance, user, wrong_secret) is False

	first_token = provider.create_token(database_client_instance, user, None, None)
	assert provider.count_tokens(database_client_instance, user) == 1
	assert provider.authenticate_with_token(database_client_instance, user, first_token["secret"]) is True
	assert provider.authenticate_with_token(database_client_instance, user, wrong_secret) is False

	second_token = provider.create_token(database_client_instance, user, None, None)
	assert provider.count_tokens(database_client_instance, user) == 2
	assert provider.authenticate_with_token(database_client_instance, user, first_token["secret"]) is True
	assert provider.authenticate_with_token(database_client_instance, user, second_token["secret"]) is True
	assert provider.authenticate_with_token(database_client_instance, user, wrong_secret) is False

	provider.delete_token(database_client_instance, user, first_token["identifier"])
	assert provider.count_tokens(database_client_instance, user) == 1
	assert provider.authenticate_with_token(database_client_instance, user, first_token["secret"]) is False
	assert provider.authenticate_with_token(database_client_instance, user, second_token["secret"]) is True
	assert provider.authenticate_with_token(database_client_instance, user, wrong_secret) is False


def test_token_expired():
	""" Test if token is refused when expired """

	database_client_instance = MemoryDatabaseClient()
	date_time_provider_instance = FakeDateTimeProvider()
	provider = AuthenticationProvider(date_time_provider_instance)

	user = "user"

	permanent_token = provider.create_token(database_client_instance, user, None, None)
	valid_token = provider.create_token(database_client_instance, user, None, datetime.timedelta(days = 1))
	expired_token = provider.create_token(database_client_instance, user, None, datetime.timedelta(days = -1))

	assert provider.authenticate_with_token(database_client_instance, user, permanent_token["secret"]) is True
	assert provider.authenticate_with_token(database_client_instance, user, valid_token["secret"]) is True
	assert provider.authenticate_with_token(database_client_instance, user, expired_token["secret"]) is False


def test_hash_password_success():
	""" Test hash_password succeeds in a normal situation """

	date_time_provider_instance = FakeDateTimeProvider()
	provider = AuthenticationProvider(date_time_provider_instance)

	secret = "password"
	salt = secrets.token_hex(provider.password_salt_size)
	provider.hash_password(secret, salt, provider.password_hash_function, provider.password_hash_function_parameters)


def test_hash_password_determinist():
	""" Test hash_password returns a determinist result """

	date_time_provider_instance = FakeDateTimeProvider()
	provider = AuthenticationProvider(date_time_provider_instance)

	secret = "password"
	salt = secrets.token_hex(provider.password_salt_size)
	first_password_hash = provider.hash_password(secret, salt, provider.password_hash_function, provider.password_hash_function_parameters)
	second_password_hash = provider.hash_password(secret, salt, provider.password_hash_function, provider.password_hash_function_parameters)

	assert first_password_hash == second_password_hash


def test_hash_token_success():
	""" Test hash_token succeeds in a normal situation """

	date_time_provider_instance = FakeDateTimeProvider()
	provider = AuthenticationProvider(date_time_provider_instance)

	secret = secrets.token_hex(provider.token_size)
	provider.hash_token(secret, provider.token_hash_function, provider.token_hash_function_parameters)


def test_hash_token_determinist():
	""" Test hash_token returns a determinist result """

	date_time_provider_instance = FakeDateTimeProvider()
	provider = AuthenticationProvider(date_time_provider_instance)

	secret = secrets.token_hex(provider.token_size)
	first_token_hash = provider.hash_token(secret, provider.token_hash_function, provider.token_hash_function_parameters)
	second_token_hash = provider.hash_token(secret, provider.token_hash_function, provider.token_hash_function_parameters)

	assert first_token_hash == second_token_hash

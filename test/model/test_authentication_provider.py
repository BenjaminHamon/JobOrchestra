""" Unit tests for AuthenticationProvider """

import datetime
import secrets

import bhamon_orchestra_model.authentication_provider as authentication_provider
import bhamon_orchestra_model.database.memory_database_client as memory_database_client


def test_password_success():
	""" Test password operations succeed in a normal situation """

	database_client_instance = memory_database_client.MemoryDatabaseClient()
	provider = authentication_provider.AuthenticationProvider(database_client_instance)

	user = "user"
	first_secret = "first"
	second_secret = "second"
	wrong_secret = "wrong"

	assert provider.authenticate_with_password(user, first_secret) is False
	assert provider.authenticate_with_password(user, second_secret) is False
	assert provider.authenticate_with_password(user, wrong_secret) is False

	provider.set_password(user, first_secret)
	assert provider.authenticate_with_password(user, first_secret) is True
	assert provider.authenticate_with_password(user, second_secret) is False
	assert provider.authenticate_with_password(user, wrong_secret) is False

	provider.set_password(user, second_secret)
	assert provider.authenticate_with_password(user, first_secret) is False
	assert provider.authenticate_with_password(user, second_secret) is True
	assert provider.authenticate_with_password(user, wrong_secret) is False

	provider.remove_password(user)
	assert provider.authenticate_with_password(user, first_secret) is False
	assert provider.authenticate_with_password(user, second_secret) is False
	assert provider.authenticate_with_password(user, wrong_secret) is False


def test_token_success():
	""" Test token operations succeed in a normal situation """

	database_client_instance = memory_database_client.MemoryDatabaseClient()
	provider = authentication_provider.AuthenticationProvider(database_client_instance)

	user = "user"
	wrong_secret = secrets.token_hex(provider.token_size)

	assert provider.count_tokens(user) == 0
	assert provider.authenticate_with_token(user, wrong_secret) is False

	first_token = provider.create_token(user, None, None)
	assert provider.count_tokens(user) == 1
	assert provider.authenticate_with_token(user, first_token["secret"]) is True
	assert provider.authenticate_with_token(user, wrong_secret) is False

	second_token = provider.create_token(user, None, None)
	assert provider.count_tokens(user) == 2
	assert provider.authenticate_with_token(user, first_token["secret"]) is True
	assert provider.authenticate_with_token(user, second_token["secret"]) is True
	assert provider.authenticate_with_token(user, wrong_secret) is False

	provider.delete_token(user, first_token["identifier"])
	assert provider.count_tokens(user) == 1
	assert provider.authenticate_with_token(user, first_token["secret"]) is False
	assert provider.authenticate_with_token(user, second_token["secret"]) is True
	assert provider.authenticate_with_token(user, wrong_secret) is False


def test_token_expired():
	""" Test if token is refused when expired """

	database_client_instance = memory_database_client.MemoryDatabaseClient()
	provider = authentication_provider.AuthenticationProvider(database_client_instance)

	user = "user"

	permanent_token = provider.create_token(user, None, None)
	valid_token = provider.create_token(user, None, datetime.timedelta(days = 1))
	expired_token = provider.create_token(user, None, datetime.timedelta(days = -1))

	assert provider.authenticate_with_token(user, permanent_token["secret"]) is True
	assert provider.authenticate_with_token(user, valid_token["secret"]) is True
	assert provider.authenticate_with_token(user, expired_token["secret"]) is False


def test_hash_password_success():
	""" Test hash_password succeeds in a normal situation """

	database_client_instance = memory_database_client.MemoryDatabaseClient()
	provider = authentication_provider.AuthenticationProvider(database_client_instance)

	secret = "password"
	salt = secrets.token_hex(provider.password_salt_size)
	provider.hash_password(secret, salt, provider.password_hash_function, provider.password_hash_function_parameters)


def test_hash_password_determinist():
	""" Test hash_password returns a determinist result """

	database_client_instance = memory_database_client.MemoryDatabaseClient()
	provider = authentication_provider.AuthenticationProvider(database_client_instance)

	secret = "password"
	salt = secrets.token_hex(provider.password_salt_size)
	first_password_hash = provider.hash_password(secret, salt, provider.password_hash_function, provider.password_hash_function_parameters)
	second_password_hash = provider.hash_password(secret, salt, provider.password_hash_function, provider.password_hash_function_parameters)

	assert first_password_hash == second_password_hash


def test_hash_token_success():
	""" Test hash_token succeeds in a normal situation """

	database_client_instance = memory_database_client.MemoryDatabaseClient()
	provider = authentication_provider.AuthenticationProvider(database_client_instance)

	secret = secrets.token_hex(provider.token_size)
	provider.hash_token(secret, provider.token_hash_function, provider.token_hash_function_parameters)


def test_hash_token_determinist():
	""" Test hash_token returns a determinist result """

	database_client_instance = memory_database_client.MemoryDatabaseClient()
	provider = authentication_provider.AuthenticationProvider(database_client_instance)

	secret = secrets.token_hex(provider.token_size)
	first_token_hash = provider.hash_token(secret, provider.token_hash_function, provider.token_hash_function_parameters)
	second_token_hash = provider.hash_token(secret, provider.token_hash_function, provider.token_hash_function_parameters)

	assert first_token_hash == second_token_hash

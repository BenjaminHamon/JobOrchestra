# Security

Orchestra includes a simple implementation of user and authorization.

Most operations require a token, which the application uses to authenticate the user making the request, and then checks their authorization. The token must be sent with the user name, using basic authentication.

For production, it is strongly recommended to set up SSL and use secure protocols, HTTPS and WSS. It is also important to secure access to the database and to the file storage.

On setup, use the CLI to create the first administrator user.


## User

A user is created by an administrator. It is identified by a unique name.

Each user can be assigned a number of roles, which provides them with authorizations. Additionally, a user may be disabled, reducing their authorizations to those of an anonymous user.

The standard roles are:
* Anonymous (automatic, not logged in): minimal access to web routes (home, help, login, static)
* Default (automatic, logged in): minimal access to web routes (home, help, me, service proxy, static)
* Administrator: full read-write access to web routes
* Auditor: full read access to web routes
* Operator: write access to web routes by whitelist (all but administration)
* Viewer: read access to web routes by whitelist (all but administration)
* Worker: connection access to the master, access to web routes for triggering jobs and viewing runs



## Password

A user may have a password. This password is only used with the login on the website and on the service. The login operation returns a new authentication token which is used for all other operations.

Passwords are stored in the database, hashed, with salt, using PBKDF2 with SHA-256 and a million iterations by default.

Usually, service users, for use by other application or scripts, should not have a password and would not login, instead an administrator manages their tokens directly.


## Token

A user may have many authentication tokens. A token may have an expiration date. A token is created after each login.

For the website, after login, the token is saved to the user session and is passed with each request. The session is stored encrypted in a cookie. The website refreshes the session token every day and expires it after a week without activity.

A token must be sent with every request, using basic authentication.

Tokens are generated, with a secure random, as hexadecimal strings, of 32 bytes by default. They are stored in the database, hashed with SHA-256 by default.


## Worker

A worker authenticates itself with the master when connecting, by sending a request with basic authentication, then the connection stays open between the two.

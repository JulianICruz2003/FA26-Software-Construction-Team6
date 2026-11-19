# Backend authentication

The authentication API uses email and password credentials. The current desktop
app does not send credentials. Project, task, user-directory, and membership
routes remain open for local development until the authorization work lands.

## Migration and existing accounts

Update the server's Python dependencies, then apply migrations to the intended
database before starting the updated API.

```bash
python -m pip install -r requirements/server.txt
python -m alembic upgrade head
```

Revision `6c7ab719eb23` adds a nullable `users.password_hash` column and a new
`auth_sessions` table. Existing users, projects, tasks, and memberships remain
in place. Existing users start without credentials. They cannot log in, and
self-registration with an existing email cannot take over the account.

A trusted administrator with access to the server terminal and its database
configuration can create a Professor or activate a passwordless account. Verify
the account owner's identity and intended role before provisioning. In
particular, a legacy `Professor` label was previously assignable through the
development API and is insufficient evidence of approval.

```bash
# Create a Professor account.
python -m server.provision_account --email professor@example.com --role Professor --name "Professor Name"

# Activate an existing, verified account in place.
python -m server.provision_account --email student@example.com --role Student
```

Use the intended role explicitly when activating a verified legacy Professor.
The command prompts twice with hidden input and refuses to replace existing
credentials. Use a unique password chosen by the account owner through a
trusted process. The command preserves existing user IDs and memberships.
Legacy addresses must be valid for sign-in. Resolve invalid addresses with the
administrator before activation. The migration downgrade removes password hashes
and session rows, so it would discard accounts' credentials and sessions.

The legacy `POST /users` route creates only passwordless Student records. The
current desktop team dialog may still show a Professor option. The API rejects
that selection, and Professor accounts must be provisioned from the server.

## Endpoints

| Method and path | Request and response |
| --- | --- |
| `POST /auth/register` | Accepts `name`, `email`, and `password`. Returns 201 and the Student profile, or 409 for an existing email. Role fields are rejected. |
| `POST /auth/login` | Accepts `email` and `password`. Returns `access_token`, `token_type` (`bearer`), and `expires_at`. Invalid credentials and passwordless accounts receive the same 401 response. |
| `GET /auth/me` | Accepts `Authorization: Bearer <token>` and returns the profile. |
| `POST /auth/logout` | Accepts the same authorization header, revokes that session, and returns 204. Other sessions remain active. |

Emails are validated and normalized for lookup. New passwords must contain 15
to 128 characters. Passwords are stored using salted Argon2id hashes. The API
can rehash an existing password on successful login when hashing parameters
change. Validation errors on authentication routes omit submitted values.

Each login generates an opaque token from 32 bytes of randomness. PostgreSQL
stores only its SHA-256 digest, the user ID, and a fixed 12-hour expiration.
Logout removes the session row. Expired tokens cannot authenticate. There is
no refresh-token flow. The desktop login work can send the bearer token in
the authorization header and prompt for sign-in again on expiry. Avoid logging
tokens or sending them in URLs.

Use HTTPS for credentials and bearer tokens outside loopback. Before shared
deployment, enforce authentication and project permissions on business routes
and add login throttling and expired-session cleanup. Student self-registration
does not verify ownership of an email address.

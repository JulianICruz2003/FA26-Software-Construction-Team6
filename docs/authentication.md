# Account registration and authentication

## Register from the desktop

Follow the [local setup instructions](../README.md#run-locally-macos-linux-or-windows)
to start PostgreSQL, apply Alembic migrations, and launch FastAPI. Run
`python -m desktop.main` from the repository root.

1. Select **Create Account** on the Sign In window.
2. Enter your full name and a valid address at exactly `@miners.utep.edu` or
   `@utep.edu`. Domain matching is case insensitive. The API stores email
   addresses in lowercase.
3. Enter and confirm a password of 8–128 characters with at least one number
   and one punctuation character or symbol. Letters of either case are optional.
4. Submit the form, acknowledge the confirmation, and sign in with your new
   credentials to open the Student Dashboard.

The PySide6 dialog masks both password fields and checks the form before HTTPX
sends the name, email, and password to `POST /auth/register` on `API_BASE_URL`.
FastAPI validates the request again. Public registration always creates a Student
and returns a profile. Sign-in creates the bearer session in a separate request.

To test with a local development database, register with an unused university
address, sign in, and sign out. Repeat with the same email to check duplicate
handling. Try another domain and a nonmatching confirmation to check the form
errors. Run `python -m pytest -q` for automated tests. With Docker running,
`RUN_POSTGRES_TESTS=1 python -m pytest -q` includes integration tests in a
disposable PostgreSQL container.

## Existing accounts and administrator provisioning

Registration uses the existing schema. Revision `6c7ab719eb23` introduced
`users.password_hash` and `auth_sessions`. Existing records and memberships
are preserved. Accounts with credentials can still sign in using their
existing email and password. Passwordless records cannot sign in, and
self-registration with an existing email cannot take over the record.

A trusted administrator with access to the server terminal and database can
create a Professor account or activate a passwordless record. Verify the
account owner's identity and intended role before provisioning. Treat legacy
Professor labels as unverified because the old development API allowed clients
to set them.

```bash
python -m server.provision_account --email professor@utep.edu --role Professor --name "Professor Name"
python -m server.provision_account --email student@miners.utep.edu --role Student
```

The command prompts twice with hidden input, enforces the university email and
new password rules, and refuses to replace existing credentials. Activation
preserves user IDs and memberships and requires an eligible university address.
Use the intended role explicitly. The legacy `POST /users` route creates only
passwordless Student records with a university email so Team management can
continue to create development records.

## Endpoints and credential storage

| Method and path | Request and response |
| --- | --- |
| `POST /auth/register` | Accepts `name`, `email`, and `password`. Returns 201 and the Student profile, or 409 for an existing email. Role fields are rejected. |
| `POST /auth/login` | Accepts `email` and `password`. Returns `access_token`, `token_type` (`bearer`), and `expires_at`. Invalid credentials and passwordless accounts receive the same 401 response. |
| `GET /auth/me` | Accepts `Authorization: Bearer <token>` and returns the profile. |
| `POST /auth/logout` | Accepts the same authorization header, revokes that session, and returns 204. Other sessions remain active. |

Passwords are stored as salted Argon2id hashes. The API can rehash an existing
password on successful login when hashing parameters change. Validation errors
on authentication and account-creation routes omit submitted input values.

Each login generates an opaque token from 32 bytes of randomness. PostgreSQL
stores only its SHA-256 digest, user ID, and fixed 12-hour expiration. The
desktop holds the bearer token in memory. Logout removes the session row.
Expired tokens cannot authenticate. A user signs in again to start a new session.

## Shared deployment limitations

The email domain check establishes address eligibility. Verification of email
ownership remains future work. Project, task, user-directory, and membership
routes are open in the local development prototype. Enforce authentication and
project permissions before shared deployment. Use HTTPS outside loopback and
add login throttling and expired-session cleanup.

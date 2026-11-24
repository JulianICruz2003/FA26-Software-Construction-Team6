from datetime import UTC, datetime, timedelta
from hashlib import sha256

from argon2 import PasswordHasher
import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from server.auth import PASSWORD_HASHER
from server.models import AuthSession, User
from server.provision_account import provision_account


PASSWORD = "miners123!"
STUDENT = {
    "name": "Test Student", "email": "student@miners.utep.edu", "password": PASSWORD
}


@pytest.fixture
def student(api):
    response = api.post("/auth/register", json=STUDENT)
    assert response.status_code == 201, response.text
    return response.json()


def sign_in(api, email=STUDENT["email"], password=PASSWORD):
    return api.post("/auth/login", json={"email": email, "password": password})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_registration_persists_argon2id_and_hides_credentials(api, db_connection, student):
    assert student == {
        "id": student["id"], "name": STUDENT["name"], "email": STUDENT["email"],
        "account_role": "Student",
    }
    stored_hash = db_connection.scalar(
        select(User.password_hash).where(User.id == student["id"])
    )
    assert stored_hash.startswith("$argon2id$")
    assert PasswordHasher().verify(stored_hash, PASSWORD)
    assert PASSWORD not in stored_hash
    assert api.get("/users").json() == [student]


def test_duplicate_registration_preserves_existing_credentials(api, student):
    response = api.post("/auth/register", json={
        **STUDENT, "email": "STUDENT@MINERS.UTEP.EDU", "password": "Different123!",
    })
    assert response.status_code == 409
    assert api.get("/users").json() == [student]
    assert sign_in(api).status_code == 200


def test_login_uses_expiring_opaque_token_and_current_user(api, db_connection, student):
    before = datetime.now(UTC)
    response = sign_in(api, email="STUDENT@MINERS.UTEP.EDU")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    session = response.json()
    assert session["token_type"] == "bearer"
    token = session["access_token"]
    digest = sha256(token.encode()).hexdigest()
    row = db_connection.execute(
        select(AuthSession.__table__).where(AuthSession.token_digest == digest)
    ).mappings().one()
    assert row["user_id"] == student["id"]
    assert row["token_digest"] != token
    assert before + timedelta(hours=12) <= row["expires_at"]
    assert row["expires_at"] <= datetime.now(UTC) + timedelta(hours=12)
    assert row["expires_at"] == datetime.fromisoformat(session["expires_at"])
    current = api.get("/auth/me", headers=bearer(token))
    assert current.status_code == 200
    assert current.json() == student


def test_invalid_login_has_generic_response_and_creates_no_sessions(api, db_connection, student):
    wrong = sign_in(api, password="incorrect passphrase")
    unknown = sign_in(api, email="unknown@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Invalid email or password"}
    assert db_connection.scalar(select(AuthSession.token_digest)) is None


def test_logout_revokes_only_the_current_session(api, student):
    first = bearer(sign_in(api).json()["access_token"])
    second = bearer(sign_in(api).json()["access_token"])
    response = api.post("/auth/logout", headers=first)
    assert response.status_code == 204
    assert not response.content
    assert api.get("/auth/me", headers=first).status_code == 401
    assert api.post("/auth/logout", headers=first).status_code == 401
    assert api.get("/auth/me", headers=second).status_code == 200


def test_expired_session_cannot_authenticate(api, db_connection, student):
    token = sign_in(api).json()["access_token"]
    db_connection.execute(
        update(AuthSession)
        .where(AuthSession.token_digest == sha256(token.encode()).hexdigest())
        .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    )
    assert api.get("/auth/me", headers=bearer(token)).status_code == 401
    assert api.post("/auth/logout", headers=bearer(token)).status_code == 401


@pytest.mark.parametrize("headers", [
    {}, {"Authorization": "Basic abc"}, bearer("invalid"), bearer("a" * 43),
])
def test_current_user_and_logout_require_valid_bearer(api, headers):
    for response in (api.get("/auth/me", headers=headers), api.post("/auth/logout", headers=headers)):
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize("path", ["/auth/register", "/users"])
def test_public_user_creation_cannot_assign_professor_role(api, path):
    payload = STUDENT if path == "/auth/register" else {
        "name": STUDENT["name"], "email": STUDENT["email"],
    }
    response = api.post(path, json={**payload, "account_role": "Professor"})
    assert response.status_code == 422
    assert api.get("/users").json() == []


def test_invalid_auth_requests_do_not_echo_passwords(api):
    short_password = "KeepMeSecret"
    invalid_registration = api.post("/auth/register", json={**STUDENT, "password": short_password})
    invalid_login = sign_in(api, password=PASSWORD * 20)
    assert invalid_registration.status_code == invalid_login.status_code == 422
    assert short_password not in invalid_registration.text
    assert PASSWORD not in invalid_login.text
    assert api.get("/users").json() == []


def test_legacy_account_requires_trusted_provisioning(api, db_connection):
    email = "legacy@utep.edu"
    existing = api.post("/users", json={"name": "Legacy User", "email": email})
    assert existing.status_code == 201
    user_id = existing.json()["id"]
    assert db_connection.scalar(select(User.password_hash).where(User.id == user_id)) is None
    assert sign_in(api, email=email).status_code == 401
    assert api.post("/auth/register", json={**STUDENT, "email": email}).status_code == 409

    with Session(db_connection, join_transaction_mode="create_savepoint") as db:
        provision_account(db, email=email, password=PASSWORD, role="Student", name=None)
    session = sign_in(api, email=email)
    assert session.status_code == 200
    assert api.get("/auth/me", headers=bearer(session.json()["access_token"])).json() == existing.json()

    with Session(db_connection, join_transaction_mode="create_savepoint") as db:
        with pytest.raises(ValueError, match="already has credentials"):
            provision_account(db, email=email, password=PASSWORD, role="Professor", name=None)


def test_trusted_provisioning_can_create_professor(api, db_connection):
    email = "professor@utep.edu"
    with Session(db_connection, join_transaction_mode="create_savepoint") as db:
        provision_account(db, email=email, password=PASSWORD, role="Professor", name="Professor")
    session = sign_in(api, email=email)
    assert session.status_code == 200
    assert api.get("/auth/me", headers=bearer(session.json()["access_token"])).json() == {
        **api.get("/users").json()[0], "account_role": "Professor",
    }


def test_utep_registration_normalizes_email(api):
    response = api.post("/auth/register", json={**STUDENT, "email": " Student@UTEP.EDU "})
    assert response.status_code == 201
    assert response.json()["email"] == "student@utep.edu"
    assert sign_in(api, email="student@utep.edu").status_code == 200


@pytest.mark.parametrize("path", ["/auth/register", "/users"])
@pytest.mark.parametrize("email", [
    "student@gmail.com",
    "student@fakeutep.edu",
    "student@miners.utep.edu.fake.com",
    "invalid",
])
def test_public_account_creation_requires_university_email(api, path, email):
    payload = {"name": STUDENT["name"], "email": email}
    if path == "/auth/register":
        payload["password"] = PASSWORD
    assert api.post(path, json=payload).status_code == 422
    assert api.get("/users").json() == []


@pytest.mark.parametrize("password", ["Test1!", "a" * 127 + "1!", "password!", "password1 "])
def test_registration_rejects_invalid_passwords(api, password):
    response = api.post("/auth/register", json={**STUDENT, "password": password})
    assert response.status_code == 422
    assert password not in response.text
    assert api.get("/users").json() == []


@pytest.mark.parametrize("password", ["abcdef1!", "A" * 126 + "1@"])
def test_registration_accepts_password_boundaries(api, password):
    assert api.post("/auth/register", json={**STUDENT, "password": password}).status_code == 201
    assert sign_in(api, password=password).status_code == 200


@pytest.mark.parametrize(("email", "password"), [
    ("professor@example.com", PASSWORD),
    ("professor@utep.edu", "legacy passphrase"),
])
def test_trusted_provisioning_requires_new_account_policy(db_connection, email, password):
    with Session(db_connection, join_transaction_mode="create_savepoint") as db:
        with pytest.raises(ValueError):
            provision_account(db, email=email, password=password, role="Professor", name="Professor")
        assert db.scalar(select(User.id)) is None


@pytest.mark.parametrize("role", ["Student", "Professor"])
def test_existing_credentials_work_without_new_account_policy(api, db_connection, role):
    email = "existing@example.com"
    password = "legacy passphrase"
    db_connection.execute(User.__table__.insert().values(
        name="Existing User", email=email, account_role=role,
        password_hash=PASSWORD_HASHER.hash(password),
    ))
    response = sign_in(api, email=email, password=password)
    assert response.status_code == 200
    assert api.get("/auth/me", headers=bearer(response.json()["access_token"])).json()["account_role"] == role


def test_development_user_route_does_not_echo_unexpected_password(api):
    response = api.post("/users", json=STUDENT)
    assert response.status_code == 422
    assert PASSWORD not in response.text
    assert api.get("/users").json() == []

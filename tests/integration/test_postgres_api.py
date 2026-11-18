from pathlib import Path

from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import inspect, text


def created(api, path, **payload):
    response = api.post(path, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_migrated_database_is_at_head(postgres_engine, api):
    scripts = ScriptDirectory(str(Path(__file__).resolve().parents[2] / "alembic"))
    with postgres_engine.connect() as connection:
        assert MigrationContext.configure(connection).get_current_heads() == tuple(
            scripts.get_heads()
        )
        assert {"projects", "tasks", "users", "project_memberships"} <= set(
            inspect(connection).get_table_names()
        )
    response = api.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_migrated_foreign_keys_cascade_on_project_deletion(postgres_engine):
    with postgres_engine.connect() as connection, connection.begin() as transaction:
        project_id = connection.scalar(text(
            "INSERT INTO projects (name, description) VALUES ('Survey', '') RETURNING id"
        ))
        user_id = connection.scalar(text(
            "INSERT INTO users (name, email, account_role) "
            "VALUES ('Student', 'student@example.com', 'Student') RETURNING id"
        ))
        ids = {"project_id": project_id, "user_id": user_id}
        connection.execute(text(
            "INSERT INTO tasks (project_id, title) VALUES (:project_id, 'Map site')"
        ), ids)
        connection.execute(text(
            "INSERT INTO project_memberships (project_id, user_id, project_role) "
            "VALUES (:project_id, :user_id, 'Member')"
        ), ids)
        connection.execute(text("DELETE FROM projects WHERE id = :project_id"), ids)
        assert connection.scalar(text(
            "SELECT count(*) FROM tasks WHERE project_id = :project_id"
        ), ids) == 0
        assert connection.scalar(text(
            "SELECT count(*) FROM project_memberships WHERE project_id = :project_id"
        ), ids) == 0
        assert connection.scalar(text(
            "SELECT id FROM users WHERE id = :user_id"
        ), ids) == user_id
        transaction.rollback()


def test_projects_round_trip_metadata_and_default_fields(api):
    payload = {
        "name": "Field survey",
        "description": "Map the site",
        "deadline": "2027-01-31",
        "team_name": "Survey team",
    }
    first = created(api, "/projects", **payload)
    assert first == {"id": first["id"], **payload}
    second = created(api, "/projects", name="Another project")
    assert second == {
        "id": second["id"], "name": "Another project",
        "description": "", "deadline": None, "team_name": None,
    }
    response = api.get("/projects")
    assert response.status_code == 200
    assert response.json() == [second, first]


def test_tasks_are_project_scoped_and_completion_is_reversible(api):
    project = created(api, "/projects", name="First")
    other = created(api, "/projects", name="Second")
    tasks = f"/projects/{project['id']}/tasks"
    other_tasks = f"/projects/{other['id']}/tasks"
    task = created(api, tasks, title="  Review findings  ")
    assert task == {
        "id": task["id"], "project_id": project["id"],
        "title": "Review findings", "is_complete": False,
    }
    assert api.get(tasks).json() == [task]
    assert api.get(other_tasks).json() == []
    assert api.patch(
        f"{other_tasks}/{task['id']}", json={"is_complete": True}
    ).status_code == 404
    assert api.get(tasks).json() == [task]

    for completed in (True, False):
        response = api.patch(f"{tasks}/{task['id']}", json={"is_complete": completed})
        assert response.status_code == 200
        expected = {**task, "is_complete": completed}
        assert response.json() == expected
        assert api.get(tasks).json() == [expected]


def test_users_normalize_email_and_reject_duplicates(api):
    user = created(api, "/users", name="  Example User  ", email=" Student@Example.com ")
    assert user == {
        "id": user["id"], "name": "Example User",
        "email": "student@example.com", "account_role": "Student",
    }
    response = api.post(
        "/users", json={"name": "Duplicate", "email": "STUDENT@example.com"}
    )
    assert response.status_code == 409
    assert api.get("/users").json() == [user]


def test_membership_add_list_duplicate_and_remove(api):
    project = created(api, "/projects", name="First")
    other = created(api, "/projects", name="Second")
    user = created(api, "/users", name="Student", email="student@example.com")
    members = f"/projects/{project['id']}/members"
    other_members = f"/projects/{other['id']}/members"
    assignment = {"user_id": user["id"], "project_role": "Team Lead"}
    member = created(api, members, **assignment)
    assert member == {
        **user, **assignment, "id": member["id"],
    }
    assert api.post(members, json=assignment).status_code == 409
    assert api.get(members).json() == [member]
    assert api.get(other_members).json() == []
    assert api.delete(f"{other_members}/{member['id']}").status_code == 404
    assert api.get(members).json() == [member]
    assert api.delete(f"{members}/{member['id']}").status_code == 204
    assert api.get(members).json() == []
    assert api.get("/users").json() == [user]


@pytest.mark.parametrize(
    ("method", "path", "body", "expected"),
    [
        ("POST", "/projects", {"name": " "}, 422),
        ("POST", "/projects", {"name": "Survey", "deadline": "2027-02-30"}, 422),
        ("POST", "/projects/-1/tasks", {"title": " "}, 422),
        ("PATCH", "/projects/-1/tasks/-1", {"is_complete": "invalid"}, 422),
        ("POST", "/users", {"name": "Student", "email": "invalid"}, 422),
        ("POST", "/users", {"name": "Student", "email": "s@example.com", "account_role": "Invalid"}, 422),
        ("POST", "/projects/-1/members", {"user_id": 0}, 422),
        ("POST", "/projects/-1/members", {"user_id": 1, "project_role": "Invalid"}, 422),
        ("GET", "/projects/-1/tasks", None, 404),
        ("POST", "/projects/-1/tasks", {"title": "Missing project"}, 404),
        ("PATCH", "/projects/-1/tasks/-1", {"is_complete": True}, 404),
        ("GET", "/projects/-1/members", None, 404),
        ("POST", "/projects/-1/members", {"user_id": 1}, 404),
        ("DELETE", "/projects/-1/members/-1", None, 404),
    ],
)
def test_invalid_requests_and_missing_resources(api, method, path, body, expected):
    response = api.request(method, path, json=body)
    assert response.status_code == expected, response.text


def test_membership_requires_existing_user(api):
    project = created(api, "/projects", name="Survey")
    response = api.post(f"/projects/{project['id']}/members", json={"user_id": 1})
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

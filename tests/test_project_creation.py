import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from desktop.dialogs.create_project import CreateProjectDialog
from desktop.pages.projects import ProjectsPage
from desktop.pages.workspace.overview import OverviewTab
from desktop.services import api_client
from server.database import get_session
from server.main import app
from server.models import Project


@pytest.fixture
def project_api():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Project.__table__.create(engine)

    def test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session)
        engine.dispose()


def test_desktop_submits_and_displays_all_project_fields(qt_widget, monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://testserver")
    deadline = QDate.currentDate().addDays(14)
    projects = []
    expected = {
        "name": "Field survey",
        "description": "Map the site",
        "deadline": deadline.toString("yyyy-MM-dd"),
        "team_name": "Survey team",
    }

    def handle_request(request):
        assert request.url.path == "/projects"
        if request.method == "POST":
            payload = json.loads(request.content)
            assert payload == expected
            projects.append({"id": 1, **payload})
            return httpx.Response(201, json=projects[-1])
        assert request.method == "GET"
        return httpx.Response(200, json=projects)

    def fill_form(dialog):
        dialog.project_name.setText("Field survey")
        dialog.description.setPlainText("Map the site")
        dialog.deadline.setDate(deadline)
        dialog.team_name.setText("Survey team")
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(CreateProjectDialog, "exec", fill_form)
    transport = httpx.MockTransport(handle_request)
    monkeypatch.setattr(
        api_client, "httpx",
        SimpleNamespace(Client=lambda **kwargs: httpx.Client(transport=transport, **kwargs)),
    )

    page = qt_widget(ProjectsPage, api_client.ApiClient())
    page.create_button.click()

    assert projects == [{"id": 1, **expected}]
    assert page.project_list.count() == 1
    overview = qt_widget(OverviewTab)
    page.project_opened.connect(overview.set_project)
    page.open_selected_project(page.project_list.item(0))
    assert overview.description.text() == expected["description"]
    assert overview.deadline_label.text() == expected["deadline"]
    assert overview.team_name_label.text() == expected["team_name"]


def test_api_persists_all_project_fields(project_api):
    payload = {
        "name": "Field survey",
        "description": "Map the site",
        "deadline": "2026-12-20",
        "team_name": "Survey team",
    }
    response = project_api.post("/projects", json=payload)
    assert response.status_code == 201
    assert response.json() == {"id": 1, **payload}
    assert project_api.get("/projects").json() == [response.json()]


def test_original_create_payload_still_works(project_api):
    response = project_api.post(
        "/projects", json={"name": "Existing client", "description": "No metadata"}
    )
    assert response.status_code == 201
    assert response.json()["deadline"] is None
    assert response.json()["team_name"] is None
    assert project_api.get("/projects").json() == [response.json()]


@pytest.mark.parametrize("fields", [{"deadline": "2026-02-30"}, {"team_name": "x" * 121}])
def test_invalid_project_metadata_is_rejected(project_api, fields):
    response = project_api.post("/projects", json={"name": "Invalid", **fields})
    assert response.status_code == 422
    assert project_api.get("/projects").json() == []

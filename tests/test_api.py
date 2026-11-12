"""FastAPI smoke tests that don't need the database online."""
from fastapi.testclient import TestClient

from server.main import app


def test_api_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "miner-project-hub-api",
    }

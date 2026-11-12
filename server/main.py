"""Local development API; do not expose publicly before adding security."""
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from server.routes.projects import router as projects_router
from server.routes.teams import router as teams_router
from server.routes.users import router as users_router

from server.database import get_engine

from server.routes.tasks import router as tasks_router

app = FastAPI(title="Miner Project Hub API", version="0.1.0")
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(teams_router)
app.include_router(users_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Indicates the HTTP API is running; does not require PostgreSQL."""
    return {"status": "ok", "service": "miner-project-hub-api"}


@app.get("/health/db")
def db_health() -> dict[str, str]:
    """Confirms the PostgreSQL connection is responding."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "database": "connected"}

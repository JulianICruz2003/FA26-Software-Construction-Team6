"""PostgreSQL fixtures backed by a fresh Docker container per test run."""

import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from server.database import get_session
from server.main import app


ROOT = Path(__file__).resolve().parents[2]


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True, timeout=120).strip()


@pytest.fixture(scope="session")
def postgres_engine():
    if os.getenv("RUN_POSTGRES_TESTS") != "1":
        pytest.skip("Set RUN_POSTGRES_TESTS=1 to start disposable PostgreSQL in Docker")

    container = docker(
        "run", "--rm", "--detach",
        "--tmpfs", "/var/lib/postgresql/data",
        "--publish", "127.0.0.1::5432",
        "--env", "POSTGRES_USER=miner_test",
        "--env", "POSTGRES_PASSWORD=miner_test",
        "--env", "POSTGRES_DB=miner_test",
        "postgres:17-alpine",
    )
    try:
        port = docker("port", container, "5432/tcp").rsplit(":", 1)[1]
        engine = create_engine(
            f"postgresql+psycopg://miner_test:miner_test@127.0.0.1:{port}/miner_test",
            connect_args={"connect_timeout": 2},
        )
        try:
            deadline = time.monotonic() + 30
            while True:
                try:
                    with engine.connect():
                        break
                except OperationalError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.5)

            # Alembic loads .env without overriding these explicit container values.
            migration_env = dict(
                os.environ,
                POSTGRES_HOST="127.0.0.1",
                POSTGRES_PORT=port,
                POSTGRES_USER="miner_test",
                POSTGRES_PASSWORD="miner_test",
                POSTGRES_DB="miner_test",
            )
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=ROOT, env=migration_env, check=True, timeout=60,
            )
            subprocess.run(
                [sys.executable, "-m", "alembic", "check"],
                cwd=ROOT, env=migration_env, check=True, timeout=60,
            )
            yield engine
        finally:
            engine.dispose()
    finally:
        docker("stop", container)


@pytest.fixture
def api(postgres_engine, monkeypatch):
    # Each request can commit its own savepoint. Roll back the outer transaction
    # to isolate each test, even when multiple API calls write rows.
    with postgres_engine.connect() as connection:
        transaction = connection.begin()

        def get_test_session():
            with Session(
                connection,
                autoflush=False,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            ) as session:
                yield session

        with monkeypatch.context() as patch:
            patch.setitem(app.dependency_overrides, get_session, get_test_session)
            patch.setattr("server.main.get_engine", lambda: postgres_engine)
            try:
                with TestClient(app) as client:
                    yield client
            finally:
                transaction.rollback()

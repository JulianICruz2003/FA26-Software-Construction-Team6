"""Local development PostgreSQL connection configuration."""
import os
from pathlib import Path
from functools import lru_cache
from urllib.parse import quote

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def database_url() -> str:
    user = quote(os.environ.get("POSTGRES_USER", "minerhub"), safe="")
    password = quote(os.environ.get("POSTGRES_PASSWORD", ""), safe="")
    host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("POSTGRES_PORT", "5432")
    name = quote(os.environ.get("POSTGRES_DB", "minerhub"), safe="")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


@lru_cache(maxsize=1)
def get_engine():
    """Open the database engine only when required by a database endpoint."""
    return create_engine(database_url(), pool_pre_ping=True)


def get_session():
    """A new session for future authorized database operations."""
    session_factory = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    with session_factory() as session:
        yield session

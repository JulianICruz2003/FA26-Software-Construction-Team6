"""Password hashing and opaque bearer session handling."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
import re
from secrets import token_urlsafe
from typing import Annotated

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from server.database import get_session
from server.models import AuthSession


SESSION_LIFETIME = timedelta(hours=12)
PASSWORD_HASHER = PasswordHasher(type=Type.ID)
DUMMY_HASH = PASSWORD_HASHER.hash(token_urlsafe(32))
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}")
bearer_scheme = HTTPBearer(auto_error=False)


class CredentialRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError as error:
                # FastAPI's default 422 can echo invalid request inputs.
                details = [
                    {key: item[key] for key in ("loc", "type")}
                    for item in error.errors()
                ]
                return JSONResponse({"detail": details}, status_code=422)

        return handle


def verify_password(password: str, stored_hash: str | None) -> bool:
    try:
        PASSWORD_HASHER.verify(stored_hash or DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return False
    return stored_hash is not None


def token_digest(token: str) -> str:
    return sha256(token.encode("ascii")).hexdigest()


def authentication_required(detail: str = "Invalid or expired session") -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})


def require_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_session)],
) -> AuthSession:
    if credentials is None or not TOKEN_PATTERN.fullmatch(credentials.credentials):
        raise authentication_required()

    session = db.get(AuthSession, token_digest(credentials.credentials))
    if session is None or session.expires_at <= datetime.now(UTC):
        raise authentication_required()
    return session

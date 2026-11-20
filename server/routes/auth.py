from datetime import UTC, datetime
from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.auth import (
    CredentialRoute,
    PASSWORD_HASHER,
    SESSION_LIFETIME,
    authentication_required,
    require_session,
    token_digest,
    verify_password,
)
from server.database import get_session
from server.models import AuthSession, User
from server.schemas import Login, SessionRead, StudentRegistration, UserRead


router = APIRouter(prefix="/auth", tags=["Authentication"], route_class=CredentialRoute)
Database = Annotated[Session, Depends(get_session)]
ActiveSession = Annotated[AuthSession, Depends(require_session)]


@router.post("/register", status_code=201, response_model=UserRead)
def register(data: StudentRegistration, db: Database):
    user = User(
        name=data.name,
        email=data.email,
        account_role="Student",
        password_hash=PASSWORD_HASHER.hash(data.password.get_secret_value()),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists") from exc
    return user


@router.post("/login", response_model=SessionRead)
def login(data: Login, response: Response, db: Database):
    user = db.scalar(select(User).where(User.email == data.email))
    password = data.password.get_secret_value()
    stored_hash = user.password_hash if user else None
    verified = verify_password(password, stored_hash)
    if user is None or stored_hash is None or not verified:
        raise authentication_required("Invalid email or password")

    if PASSWORD_HASHER.check_needs_rehash(stored_hash):
        user.password_hash = PASSWORD_HASHER.hash(password)
    token = token_urlsafe(32)
    expires_at = datetime.now(UTC) + SESSION_LIFETIME
    db.add(AuthSession(
        token_digest=token_digest(token), user_id=user.id, expires_at=expires_at
    ))
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return SessionRead(access_token=token, expires_at=expires_at)


@router.get("/me", response_model=UserRead)
def current_user(session: ActiveSession, db: Database):
    user = db.get(User, session.user_id)
    if user is None:
        raise authentication_required()
    return user


@router.post("/logout", status_code=204)
def logout(session: ActiveSession, db: Database):
    db.execute(delete(AuthSession).where(AuthSession.token_digest == session.token_digest))
    db.commit()

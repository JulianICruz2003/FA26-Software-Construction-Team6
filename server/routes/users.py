from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.database import get_session
from server.models import User
from server.schemas import UserCreate, UserRead


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_session)
):
    statement = select(User).order_by(User.name, User.id)
    return db.scalars(statement).all()


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_session)
):
    user = User(
        name=data.name,
        email=data.email,
        account_role=data.account_role
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists"
        ) from error

    db.refresh(user)
    return user
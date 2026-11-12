
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.database import get_session
from server.models import Project, User, ProjectMembership
from server.schemas import TeamMemberCreate, TeamMemberRead


router = APIRouter(
    prefix="/projects/{project_id}/members",
    tags=["Teams"]
)


def member_response(membership, user):
    return {
        "id": membership.id,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "account_role": user.account_role,
        "project_role": membership.project_role,
    }


@router.get("", response_model=list[TeamMemberRead])
def list_members(
    project_id: int,
    db: Session = Depends(get_session)
):
    if db.get(Project, project_id) is None:
        raise HTTPException(404, "Project not found")

    statement = (
        select(ProjectMembership, User)
        .join(User, ProjectMembership.user_id == User.id)
        .where(ProjectMembership.project_id == project_id)
        .order_by(ProjectMembership.id)
    )

    rows = db.execute(statement).all()

    return [
        member_response(membership, user)
        for membership, user in rows
    ]


@router.post(
    "",
    response_model=TeamMemberRead,
    status_code=status.HTTP_201_CREATED
)
def add_member(
    project_id: int,
    data: TeamMemberCreate,
    db: Session = Depends(get_session)
):
    if db.get(Project, project_id) is None:
        raise HTTPException(404, "Project not found")

    user = db.get(User, data.user_id)

    if user is None:
        raise HTTPException(404, "User not found")

    existing = db.scalar(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == data.user_id
        )
    )

    if existing is not None:
        raise HTTPException(409, "User is already a member")

    membership = ProjectMembership(
        project_id=project_id,
        user_id=data.user_id,
        project_role=data.project_role
    )

    db.add(membership)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Membership already exists")

    db.refresh(membership)

    return member_response(membership, user)


@router.delete(
    "/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_member(
    project_id: int,
    membership_id: int,
    db: Session = Depends(get_session)
):
    membership = db.get(ProjectMembership, membership_id)

    if membership is None or membership.project_id != project_id:
        raise HTTPException(404, "Membership not found")

    db.delete(membership)
    db.commit()

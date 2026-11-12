from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.database import get_session
from server.models import Project
from server.schemas import ProjectCreate, ProjectRead

router = APIRouter(prefix="/projects", tags=["Projects"])


# Retrieve all projects
@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_session)):
    statement = select(Project).order_by(Project.id.desc())
    return db.scalars(statement).all()


# Create a new project
@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_session)
):
    project = Project(
        name=data.name,
        description=data.description
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project

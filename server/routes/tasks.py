
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.database import get_session
from server.models import Project, Task
from server.schemas import TaskCreate, TaskRead, TaskUpdate


router = APIRouter(
    prefix="/projects/{project_id}/tasks",
    tags=["Tasks"]
)


@router.get("", response_model=list[TaskRead])
def get_tasks(
    project_id: int,
    db: Session = Depends(get_session)
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(404, "Project not found")

    statement = (
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.id)
    )

    return db.scalars(statement).all()


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED
)
def create_task(
    project_id: int,
    data: TaskCreate,
    db: Session = Depends(get_session)
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(404, "Project not found")

    task = Task(
        project_id=project_id,
        title=data.title,
        is_complete=False
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    project_id: int,
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_session)
):
    task = db.get(Task, task_id)

    if task is None or task.project_id != project_id:
        raise HTTPException(404, "Task not found")

    task.is_complete = data.is_complete

    db.commit()
    db.refresh(task)

    return task

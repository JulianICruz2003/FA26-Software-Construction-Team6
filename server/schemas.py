from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Project name cannot be empty")
        return value


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Task title cannot be empty")
        return value


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    is_complete: bool


class TaskUpdate(BaseModel):
    is_complete: bool


class TeamMemberCreate(BaseModel):
    user_id: int = Field(gt=0)
    project_role: Literal[
        "Member", "Team Lead", "Reviewer"
    ] = "Member"


class TeamMemberRead(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    account_role: str
    project_role: str

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    account_role: str

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    account_role: Literal["Student", "Professor"] = "Student"

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        value = value.strip().lower()
        if value.count("@") != 1 or " " in value:
            raise ValueError("Invalid email address")
        return value
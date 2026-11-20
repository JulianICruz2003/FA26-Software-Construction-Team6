from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from shared.registration import normalize_university_email, validate_new_password


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    deadline: date | None = None
    team_name: str | None = Field(default=None, max_length=120)

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
    deadline: date | None
    team_name: str | None


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


class NewAccount(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not (name := value.strip()):
            raise ValueError("Name cannot be empty")
        return name

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_university_email(value)


class UserCreate(NewAccount):
    account_role: Literal["Student"] = "Student"


class AuthEmail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class StudentRegistration(NewAccount):
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        validate_new_password(value.get_secret_value())
        return value


class Login(AuthEmail):
    password: SecretStr = Field(min_length=1, max_length=128)


class SessionRead(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime

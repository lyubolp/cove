"""SQLModel and Pydantic models for API keys."""

import uuid

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class APIKey(SQLModel, table=True):
    """A hashed API key owned by a user and scoped to a single project."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    key: str
    access_for_project_id: str = Field(foreign_key="project.id")


class APIKeyPublic(BaseModel):
    """Returned for list / read operations — never exposes the raw key."""

    id: str
    access_for_project_id: str


class APIKeyCreated(APIKeyPublic):
    """Returned only on create & rotate — includes the raw key value once."""

    key: str

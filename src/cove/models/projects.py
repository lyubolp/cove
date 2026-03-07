"""SQLModel models for projects and user-project access links."""

import uuid

from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    """A named project that groups configuration items.

    Public projects are readable by everyone; private projects require explicit access.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    is_public: bool


class ProjectUserLink(SQLModel, table=True):
    """Join table granting a user access to a specific project."""

    project_id: str = Field(foreign_key="project.id", primary_key=True)
    user_id: str = Field(foreign_key="user.id", primary_key=True)

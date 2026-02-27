import uuid

from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    is_public: bool


class ProjectUserLink(SQLModel, table=True):
    project_id: str = Field(foreign_key="project.id", primary_key=True)
    user_id: str = Field(foreign_key="user.id", primary_key=True)

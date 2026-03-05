import uuid

from sqlmodel import Field, SQLModel


class APIKey(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    key: str
    access_for_project_id: str = Field(foreign_key="project.id")

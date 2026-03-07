"""SQLModel models for configuration items stored within a project."""

import uuid

from sqlmodel import Field, SQLModel


class ConfigItem(SQLModel):
    """Abstract base for configuration items; provides a UUID primary key and project FK."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")


class KeyValue(ConfigItem, table=True):
    """A key-value configuration item belonging to a project.

    The ``value`` field is always stored as a plain string.
    """

    key: str
    value: str


# class JSONConfig(ConfigItem):
#     json_value: dict


# class PythonConfig(ConfigItem):
#     python_value: str

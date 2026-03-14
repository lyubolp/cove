"""SQLModel models for configuration items stored within a project."""

import uuid

from sqlalchemy import JSON as SAJson
from sqlalchemy import Column
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


class JSONConfig(ConfigItem, table=True):
    """A JSON configuration item belonging to a project.

    The ``json_value`` field is stored as a JSON TEXT column in SQLite.
    """

    key: str
    json_value: dict = Field(sa_column=Column(SAJson))


class PythonConfig(ConfigItem, table=True):
    """A Python code configuration item belonging to a project.

    The ``python_value`` field stores a Python code snippet as plain text.
    """

    key: str
    python_value: str

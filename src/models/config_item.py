import uuid
from sqlmodel import Field, SQLModel


type ValueType = str | int | float | bool


class ConfigItem(SQLModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")


class KeyValue(ConfigItem):
    key: str
    value: ValueType


class Project(SQLModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str


# class JSONConfig(ConfigItem):
#     json_value: dict


# class PythonConfig(ConfigItem):
#     python_value: str

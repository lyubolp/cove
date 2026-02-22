import uuid
from sqlmodel import Field, SQLModel


class ConfigItem(SQLModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    is_public: bool


class KeyValue(ConfigItem, table=True):
    key: str
    value: str


# class JSONConfig(ConfigItem):
#     json_value: dict


# class PythonConfig(ConfigItem):
#     python_value: str

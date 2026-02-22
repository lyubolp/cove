from typing import Annotated
from fastapi import FastAPI, Depends
from sqlmodel import create_engine, Session, select

from models.config_item import KeyValue, Project

app = FastAPI()
engine = create_engine("sqlite:///database.db")


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/health")
async def ping():
    return {"message": "healthy"}


@app.get("/project")
async def get_all_projects(session: Annotated[Session, Depends(get_session)]):
    statement = select(Project)
    results = session.exec(statement)

    return results.all()


@app.get("/key_value/{project_id}")
async def get_all_key_values(project_id: str, session: Annotated[Session, Depends(get_session)]):
    statement = select(KeyValue).where(KeyValue.project_id == project_id)
    results = session.exec(statement)

    return [{"key": item.key, "value": item.value} for item in results]


@app.get("/key_value/{project_id}/{key}")
async def get_key_value(project_id: str, key: str, session: Annotated[Session, Depends(get_session)]):
    statement = select(KeyValue).where(KeyValue.project_id == project_id, KeyValue.key == key)
    result = session.exec(statement).first()

    if result:
        return {"key": result.key, "value": result.value}
    else:
        return {"error": "Key not found"}


@app.post("/key_value/{project_id}/{key}/{value}")
async def create_key_value(project_id: str, key: str, value: str, session: Annotated[Session, Depends(get_session)]):
    item = KeyValue(project_id=project_id, key=key, value=value)

    session.add(item)
    session.commit()
    session.refresh(item)
    return {"status": "OK"}

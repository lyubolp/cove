from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from cove.models.config_item import KeyValue

from ..dependencies import get_session
from ..models.projects import Project
from ..models.users import User
from ..services.auth import (
    does_user_have_access_to_item,
    does_user_have_access_to_project,
    get_current_user_non_fatal,
)

router = APIRouter(prefix="/key_value")


@router.get("/{project_id}")
async def get_all_key_values(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
):
    project_statement = select(Project).where(KeyValue.project_id == project_id)
    project = session.exec(project_statement).first()

    if project is None:
        # TODO - this should probably be a 404 instead of a 200 with an error message
        return {"error": "Project not found"}

    accessible_items = []

    statement = select(KeyValue).where(KeyValue.project_id == project_id)

    if project.is_public:
        items = session.exec(statement)
        for item in items:
            if item.is_public:
                accessible_items.append(item)
            else:
                if current_user is not None and await does_user_have_access_to_item(session, current_user, item.id):
                    accessible_items.append(item)
    else:
        if current_user is None or not await does_user_have_access_to_project(session, current_user, project_id):
            raise HTTPException(status_code=403, detail="User does not have access to this project")
        items = session.exec(statement)
        accessible_items = list(items.all())

    return [{"key": item.key, "value": item.value} for item in accessible_items]


@router.get("/{project_id}/{key}")
async def get_key_value(project_id: str, key: str, session: Annotated[Session, Depends(get_session)]):
    statement = select(KeyValue).where(KeyValue.project_id == project_id, KeyValue.key == key)
    result = session.exec(statement).first()

    if result:
        return {"key": result.key, "value": result.value, "is_public": result.is_public}
    else:
        return {"error": "Key not found"}


@router.post("/{project_id}/{key}/{value}")
async def create_key_value(project_id: str, key: str, value: str, session: Annotated[Session, Depends(get_session)]):
    item = KeyValue(project_id=project_id, key=key, value=value, is_public=False)

    session.add(item)
    session.commit()
    session.refresh(item)
    return {"status": "OK"}


@router.patch("/{project_id}/{key}")
async def update_key_value(
    project_id: str,
    key: str,
    session: Annotated[Session, Depends(get_session)],
    value: str | None = None,
    is_public: bool | None = None,
):
    statement = select(KeyValue).where(KeyValue.project_id == project_id, KeyValue.key == key)
    item = session.exec(statement).first()

    if item is not None:
        if value is not None:
            item.value = value

        if is_public is not None:
            item.is_public = is_public

        session.add(item)
        session.commit()
        session.refresh(item)
        return {"status": "OK"}
    else:
        return {"error": "Key not found"}


@router.delete("/{project_id}/{key}")
async def delete_key_value(project_id: str, key: str, session: Annotated[Session, Depends(get_session)]):
    statement = select(KeyValue).where(KeyValue.project_id == project_id, KeyValue.key == key)
    item = session.exec(statement).first()

    if item is not None:
        session.delete(item)
        session.commit()
        return {"status": "OK"}
    else:
        return {"error": "Key not found"}

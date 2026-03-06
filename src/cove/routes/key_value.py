from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from cove.models.config_item import KeyValue

from ..dependencies import get_session
from ..models.projects import Project
from ..models.users import User
from ..services.auth.api_keys import (
    api_key_header,
    does_api_key_grant_access_to_project,
)
from ..services.auth.oauth2 import (
    does_user_have_access_to_project,
    get_current_user_non_fatal,
)

router = APIRouter(prefix="/key_value")


@router.get("/{project_id}")
async def get_all_key_values(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    project_statement = select(Project).where(Project.id == project_id)
    project = session.exec(project_statement).first()

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.is_public:
        if current_user is None and api_key is None:
            raise HTTPException(status_code=403, detail="User does not have access to this project")
        else:
            if current_user is not None and not await does_user_have_access_to_project(
                session, current_user, project_id
            ):
                raise HTTPException(status_code=403, detail="User does not have access to this project")
            elif api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
                raise HTTPException(status_code=403, detail="User does not have access to this project")

    statement = select(KeyValue).where(KeyValue.project_id == project_id)
    items = session.exec(statement)

    return [{"key": item.key, "value": item.value} for item in items]


@router.get("/{project_id}/{key}")
async def get_key_value(
    project_id: str,
    key: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    project_statement = select(Project).where(Project.id == project_id)
    project = session.exec(project_statement).first()

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # TODO - This seems to be repeated
    if not project.is_public:
        if current_user is None and api_key is None:
            raise HTTPException(status_code=403, detail="User does not have access to this project")
        else:
            if current_user is not None and not await does_user_have_access_to_project(
                session, current_user, project_id
            ):
                raise HTTPException(status_code=403, detail="User does not have access to this project")
            elif api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
                raise HTTPException(status_code=403, detail="User does not have access to this project")

    statement = select(KeyValue).where(KeyValue.project_id == project_id, KeyValue.key == key)
    result = session.exec(statement).first()

    if result is None:
        return {"error": "Key not found"}

    return {"key": result.key, "value": result.value}


@router.post("/{project_id}/{key}/{value}")
async def create_key_value(
    project_id: str,
    key: str,
    value: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    if current_user is None and api_key is None:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if current_user is not None and await does_user_have_access_to_project(session, current_user, project_id) is False:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if api_key is not None and does_api_key_grant_access_to_project(session, api_key, project_id) is False:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    item = KeyValue(project_id=project_id, key=key, value=value)

    session.add(item)

    session.commit()
    session.refresh(item)
    return {"status": "OK"}


@router.patch("/{project_id}/{key}")
async def update_key_value(
    project_id: str,
    key: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
    value: str | None = None,
    is_public: bool | None = None,
):
    if current_user is None and api_key is None:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if current_user is not None and await does_user_have_access_to_project(session, current_user, project_id) is False:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if api_key is not None and does_api_key_grant_access_to_project(session, api_key, project_id) is False:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

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
async def delete_key_value(
    project_id: str,
    key: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):

    if current_user is None and api_key is None:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if current_user is not None and await does_user_have_access_to_project(session, current_user, project_id) is False:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if api_key is not None and does_api_key_grant_access_to_project(session, api_key, project_id) is False:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    statement = select(KeyValue).where(KeyValue.project_id == project_id, KeyValue.key == key)
    item = session.exec(statement).first()

    if item is not None:
        session.delete(item)
        session.commit()
        return {"status": "OK"}
    else:
        return {"error": "Key not found"}

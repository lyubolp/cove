"""Routes for reading and writing JSON configuration items within a project."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from cove.models.config_item import JSONConfig

from ..dependencies import get_session
from ..models.projects import Project
from ..models.users import User
from ..services.auth.api_keys import api_key_header, does_api_key_grant_access_to_project
from ..services.auth.oauth2 import does_user_have_access_to_project, get_current_user_non_fatal

router = APIRouter(prefix="/json_item")


class JSONValueBody(BaseModel):
    value: dict


@router.get("/{project_id}")
async def get_all_json_items(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Return all JSON items for a project.

    Public projects are accessible anonymously. Private projects require the caller
    to be authenticated (JWT or API key) and have project access.
    """
    project = session.exec(select(Project).where(Project.id == project_id)).first()

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.is_public:
        if current_user is None and api_key is None:
            raise HTTPException(status_code=403, detail="User does not have access to this project")

        if current_user is not None and not await does_user_have_access_to_project(session, current_user, project_id):
            raise HTTPException(status_code=403, detail="User does not have access to this project")
        if api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
            raise HTTPException(status_code=403, detail="User does not have access to this project")

    items = session.exec(select(JSONConfig).where(JSONConfig.project_id == project_id))
    return [{"key": item.key, "json_value": item.json_value} for item in items]


@router.get("/{project_id}/{key}")
async def get_json_item(
    project_id: str,
    key: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Return a single JSON item by key within a project.

    Applies the same access-control rules as ``get_all_json_items``.
    Returns an error payload if the key does not exist.
    """
    project = session.exec(select(Project).where(Project.id == project_id)).first()

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.is_public:
        if current_user is None and api_key is None:
            raise HTTPException(status_code=403, detail="User does not have access to this project")

        if current_user is not None and not await does_user_have_access_to_project(session, current_user, project_id):
            raise HTTPException(status_code=403, detail="User does not have access to this project")
        if api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
            raise HTTPException(status_code=403, detail="User does not have access to this project")

    result = session.exec(select(JSONConfig).where(JSONConfig.project_id == project_id, JSONConfig.key == key)).first()

    if result is None:
        return {"error": "Key not found"}

    return {"key": result.key, "json_value": result.json_value}


@router.post("/{project_id}/{key}")
async def create_json_item(
    project_id: str,
    key: str,
    body: JSONValueBody,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Create a new JSON item in the specified project.

    Requires authentication and project access. Raises 403 if the caller lacks
    credentials or project membership.
    """
    if current_user is None and api_key is None:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if current_user is not None and not await does_user_have_access_to_project(session, current_user, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    item = JSONConfig(project_id=project_id, key=key, json_value=body.value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"status": "OK"}


@router.patch("/{project_id}/{key}")
async def update_json_item(
    project_id: str,
    key: str,
    body: JSONValueBody,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Replace the JSON value of an existing item (full replacement).

    Requires authentication and project access; raises 403 if access is denied.
    Returns an error payload if the key does not exist.
    """
    if current_user is None and api_key is None:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if current_user is not None and not await does_user_have_access_to_project(session, current_user, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    item = session.exec(select(JSONConfig).where(JSONConfig.project_id == project_id, JSONConfig.key == key)).first()

    if item is None:
        return {"error": "Key not found"}

    item.json_value = body.value
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"status": "OK"}


@router.delete("/{project_id}/{key}")
async def delete_json_item(
    project_id: str,
    key: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Delete a JSON item from a project.

    Requires authentication and project access; raises 403 if access is denied.
    Returns an error payload if the key does not exist.
    """
    if current_user is None and api_key is None:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if current_user is not None and not await does_user_have_access_to_project(session, current_user, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    item = session.exec(select(JSONConfig).where(JSONConfig.project_id == project_id, JSONConfig.key == key)).first()

    if item is None:
        return {"error": "Key not found"}

    session.delete(item)
    session.commit()
    return {"status": "OK"}

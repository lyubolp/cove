"""Routes for reading and writing Python code configuration items within a project."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from cove.models.config_item import PythonConfig

from ..dependencies import get_session
from ..models.projects import Project
from ..models.users import User
from ..services.auth.api_keys import api_key_header, does_api_key_grant_access_to_project
from ..services.auth.oauth2 import does_user_have_access_to_project, get_current_user_non_fatal

router = APIRouter(prefix="/python_item")


class PythonValueBody(BaseModel):
    value: str


@router.get("/{project_id}")
async def get_all_python_items(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Return all Python code items for a project.

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

    items = session.exec(select(PythonConfig).where(PythonConfig.project_id == project_id))
    return [{"key": item.key, "python_value": item.python_value} for item in items]


@router.get("/{project_id}/{key}")
async def get_python_item(
    project_id: str,
    key: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Return a single Python code item by key within a project.

    Applies the same access-control rules as ``get_all_python_items``.
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

    result = session.exec(
        select(PythonConfig).where(PythonConfig.project_id == project_id, PythonConfig.key == key)
    ).first()

    if result is None:
        return {"error": "Key not found"}

    return {"key": result.key, "python_value": result.python_value}


@router.post("/{project_id}/{key}")
async def create_python_item(
    project_id: str,
    key: str,
    body: PythonValueBody,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Create a new Python code item in the specified project.

    Requires authentication and project access. Raises 403 if the caller lacks
    credentials or project membership.
    """
    if current_user is None and api_key is None:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if current_user is not None and not await does_user_have_access_to_project(session, current_user, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    item = PythonConfig(project_id=project_id, key=key, python_value=body.value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"status": "OK"}


@router.patch("/{project_id}/{key}")
async def update_python_item(
    project_id: str,
    key: str,
    body: PythonValueBody,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Replace the Python code value of an existing item (full replacement).

    Requires authentication and project access; raises 403 if access is denied.
    Returns an error payload if the key does not exist.
    """
    if current_user is None and api_key is None:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if current_user is not None and not await does_user_have_access_to_project(session, current_user, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    item = session.exec(
        select(PythonConfig).where(PythonConfig.project_id == project_id, PythonConfig.key == key)
    ).first()

    if item is None:
        return {"error": "Key not found"}

    item.python_value = body.value
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"status": "OK"}


@router.delete("/{project_id}/{key}")
async def delete_python_item(
    project_id: str,
    key: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
):
    """Delete a Python code item from a project.

    Requires authentication and project access; raises 403 if access is denied.
    Returns an error payload if the key does not exist.
    """
    if current_user is None and api_key is None:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if current_user is not None and not await does_user_have_access_to_project(session, current_user, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    if api_key is not None and not does_api_key_grant_access_to_project(session, api_key, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    item = session.exec(
        select(PythonConfig).where(PythonConfig.project_id == project_id, PythonConfig.key == key)
    ).first()

    if item is None:
        return {"error": "Key not found"}

    session.delete(item)
    session.commit()
    return {"status": "OK"}

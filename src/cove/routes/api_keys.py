import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..dependencies import get_session
from ..models.api_keys import APIKey, APIKeyCreated, APIKeyPublic
from ..models.users import User
from ..services.auth.api_keys import get_api_key_hash
from ..services.auth.oauth2 import does_user_have_access_to_project, get_current_user

router = APIRouter(prefix="/api_keys")


@router.post("/{project_id}", response_model=APIKeyCreated, status_code=201)
async def create_api_key(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Generate a new API key scoped to a project. Returns the key value once."""
    if not await does_user_have_access_to_project(session, current_user, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    raw_key = str(uuid.uuid4())
    api_key = APIKey(
        user_id=current_user.id,
        key=get_api_key_hash(raw_key),
        access_for_project_id=project_id,
    )

    result_key = APIKeyCreated(
        id=api_key.id,
        key=raw_key,
        access_for_project_id=project_id,
    )

    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return result_key


@router.get("/", response_model=list[APIKeyPublic])
async def list_api_keys(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all API keys belonging to the authenticated user. Key values are not returned."""
    statement = select(APIKey).where(APIKey.user_id == current_user.id)
    return session.exec(statement).all()


@router.get("/{key_id}", response_model=APIKeyPublic)
async def get_api_key(
    key_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a single API key by id. Key value is not returned."""
    return _get_own_key_or_raise(key_id, current_user, session)


@router.patch("/{key_id}", response_model=APIKeyCreated)
async def rotate_api_key(
    key_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Rotate an API key, replacing its key value. The new key value is returned once."""
    api_key = _get_own_key_or_raise(key_id, current_user, session)
    api_key.key = str(uuid.uuid4())
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return api_key


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(
    key_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Revoke (delete) an API key."""
    api_key = _get_own_key_or_raise(key_id, current_user, session)
    session.delete(api_key)
    session.commit()


def _get_own_key_or_raise(key_id: str, current_user: User, session: Session) -> APIKey:
    """Fetch an APIKey by id and assert ownership; raises 404 / 403 as appropriate."""
    api_key = session.get(APIKey, key_id)
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    if api_key.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return api_key

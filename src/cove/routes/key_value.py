from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..dependencies import get_session
from cove.models.config_item import KeyValue


router = APIRouter(prefix="/key_value")


@router.get("/{project_id}")
async def get_all_key_values(project_id: str, session: Annotated[Session, Depends(get_session)]):
    statement = select(KeyValue).where(KeyValue.project_id == project_id)
    results = session.exec(statement)

    return [{"key": item.key, "value": item.value} for item in results]


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

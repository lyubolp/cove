from fastapi.security import APIKeyHeader
from pwdlib import PasswordHash
from sqlmodel import Session, select

from ...models.api_keys import APIKey

api_key_hasher = PasswordHash.recommended()
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    return api_key_hasher.verify(plain_api_key, hashed_api_key)


def get_api_key_hash(api_key: str) -> str:
    return api_key_hasher.hash(api_key)


def does_api_key_grant_access_to_project(session: Session, api_key_value: str, project_id: str) -> bool:
    statement = select(APIKey).where(APIKey.access_for_project_id == project_id)
    api_keys = session.exec(statement).all()

    for api_key in api_keys:
        if verify_api_key(api_key_value, api_key.key):
            return True

    return False

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import dotenv
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlmodel import Session, select

from ..dependencies import get_session
from ..models.config_item import ConfigItemUserLink
from ..models.projects import ProjectUserLink
from ..models.users import TokenData, User

dotenv.load_dotenv()
password_hasher = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/users/token", auto_error=False)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_hasher.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)


def authenticate_user(session, username: str, password: str):
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()

    if user is None:
        return False

    if not verify_password(password, user.password_hash):
        return False

    return user


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_current_user(
    session: Annotated[Session, Depends(get_session)], token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

        token_data = TokenData(user_id=user_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    statement = select(User).where(User.id == token_data.user_id)
    user = session.exec(statement).first()

    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    return user


async def get_current_user_non_fatal(
    session: Annotated[Session, Depends(get_session)], token: Annotated[str | None, Depends(oauth2_scheme_optional)]
) -> User | None:
    print(f"{token=}")
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            return None

        token_data = TokenData(user_id=user_id)
    except jwt.PyJWTError:
        return None

    statement = select(User).where(User.id == token_data.user_id)
    user = session.exec(statement).first()

    return user


async def does_user_have_access_to_project(
    session: Annotated[Session, Depends(get_session)],
    current_user: User,
    project_id: str,
) -> bool:

    statement = select(ProjectUserLink).where(
        ProjectUserLink.project_id == project_id, ProjectUserLink.user_id == current_user.id
    )

    return session.exec(statement).all() != []


async def does_user_have_access_to_item(
    session: Annotated[Session, Depends(get_session)],
    current_user: User,
    item_id: str,
) -> bool:

    statement = select(ConfigItemUserLink).where(
        ConfigItemUserLink.config_item_id == item_id, ConfigItemUserLink.user_id == current_user.id
    )

    return session.exec(statement).first() is not None


async def get_current_user_with_project_access(
    session: Annotated[Session, Depends(get_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
    project_id: str,
) -> User:
    user = await get_current_user(session, token)

    if not await does_user_have_access_to_project(session, user, project_id):
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    return user


async def get_current_user_with_item_access(
    session: Annotated[Session, Depends(get_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
    item_id: str,
) -> User:
    user = await get_current_user(session, token)

    if not await does_user_have_access_to_item(session, user, item_id):
        raise HTTPException(status_code=403, detail="User does not have access to this item")

    return user

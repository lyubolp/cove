import os
from datetime import datetime, timedelta, timezone


import dotenv
import jwt
from pydantic import BaseModel
from pwdlib import PasswordHash
from sqlmodel import select

from ..models.users import User


dotenv.load_dotenv()
password_hasher = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_hasher.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)


def authenticate_user(db, username: str, password: str):
    statement = select(User).where(User.username == username)
    user = db.exec(statement).first()

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

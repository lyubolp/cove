"""SQLModel and Pydantic models for users and JWT authentication tokens."""

import uuid

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """A registered application user with a hashed password."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str
    password_hash: str


class Token(BaseModel):
    """OAuth2 bearer-token response payload."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Decoded JWT payload carrying the authenticated user's id."""

    user_id: str | None = None

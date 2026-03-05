from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from cove.models.users import Token, User

from ..dependencies import get_session
from ..services.auth.oauth2 import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)

router = APIRouter(prefix="/users")


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/", response_model=User)
def create_user(username: str, password: str, db: Session = Depends(get_session)):
    db_user = db.exec(select(User).where(User.username == username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    password_hash = get_password_hash(password)

    user = User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/test")
def test_user_logged_in(current_user: Annotated[User, Depends(get_current_user)]):
    return {"message": f"Hello, {current_user.username}!"}

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..dependencies import get_session
from cove.models.users import User


router = APIRouter(prefix="/key_value")

import jwt
from collections.abc import Generator
from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlmodel import Session
from app.core import security
from app.models import User
from app.core.database import engine
from app.core.config import settings


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_db)]


















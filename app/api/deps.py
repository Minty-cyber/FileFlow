from collections.abc import Generator
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlmodel import Session
from app.core import security
from app.models import User, TokenInfo
from app.core.database import engine
from app.core.config import settings

import jwt
from jwt.exceptions import InvalidTokenError

use_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/users/login"
)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[Session, Depends(use_oauth2)]

def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, 
            algorithms=[security.ALGORITHM]
        )
        token_data = TokenInfo(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user
    
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_active_current_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user















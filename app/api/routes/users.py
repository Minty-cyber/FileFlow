from app.models import (
    User, 
    UserRegister,
    UserResponse, 
    Token, 
    OAuth2PasswordRequestFormEmail
       
)
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import uuid
from typing import Any, Annotated
from sqlmodel import select
from app.core.config import settings
from app.core.security import password_hasher, create_access_token
from app.api.deps import SessionDep
from app.crud import (
    create_user, 
    get_user_by_email, 
    authenticate, 
    
)
from app.core.config import settings


router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    user = get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    user_create = UserRegister.model_validate(user_in)
    new_user = create_user(session=session, user_register=user_create)
    return new_user
    

@router.post("/login")
def login_user(session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestFormEmail.as_form)]) -> Token :
    user = authenticate(session=session, email=form_data.email, password=form_data.password )
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=400, 
            detail="Inactive user"
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRATION)
    return Token(
        access_token = create_access_token(
            user.id, expires_delta= access_token_expires
        )
    )
    



















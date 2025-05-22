from app.models import (
    User, 
    UserRegister,
    UserResponse, 
    UserPublic,
    UserUpdate,
    GroupResponse,
    Token, 
    Message,
    OAuth2PasswordRequestFormEmail,
    Group,
    UserGroupLink
)
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import uuid
import logfire
from typing import Any, Annotated, List
from sqlmodel import select, delete, col, func
from app.core.config import settings
from app.core.security import password_hasher, create_access_token
from app.api.deps import SessionDep, CurrentUser, get_active_current_superuser
from app.crud import (
    create_user, 
    get_user_by_email, 
    authenticate, 
    edit_user
)
from app.core.config import settings
from app.core.security import generate_otp



router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    with logfire.span("Registering User {email}", email=user_in.email):
        user = get_user_by_email(session=session, email=user_in.email)
        if user:
            logfire.error("User with email {email} already exsits", email=user_in.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        user_create = UserRegister.model_validate(user_in)
        new_user = create_user(session=session, user_register=user_create)
        logfire.info(
            "User registered successfuly", 
            user_id=new_user.id, 
            email=new_user.email, 
            full_name=new_user.full_name 
        )
        return new_user
    

@router.post("/login")
def login_user(
    session: SessionDep, 
    form_data: Annotated[OAuth2PasswordRequestForm, 
    Depends(OAuth2PasswordRequestFormEmail.as_form)]
    ) -> Token :
    with logfire.span("Logging in user {email}", email=form_data.email):
        user = authenticate(session=session, email=form_data.email, password=form_data.password )
        if not user:
            logfire.error("Authentication failed for email {email}", email=form_data.email)
            raise HTTPException(
                status_code=400,
                detail="Incorrect email or password"
            )
        elif not user.is_active:
            logfire.error("Inactive {email} attempted login", email=form_data.email)
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
        logfire.info("User logged in successfuly", user_id=user.id, email=user.email)
 
@router.post("/login/test-token", response_model=UserPublic)    
def test_token(current_user: CurrentUser, )-> Any:
    with logfire.span("Testing token for user with {email}", email=current_user.email):
        logfire.info("Token Tested successfuly", user_id=current_user.id, email=current_user.email)
        return current_user
    
@router.get("/me", response_model=UserResponse)
def read_user_me(
    session: SessionDep, 
    current_user: CurrentUser
) -> Any:
    user_groups = session.exec(
        select(Group, UserGroupLink.role).join(UserGroupLink).where(
            UserGroupLink.user_id == current_user.id
        )
    ).all()
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        full_name = current_user.full_name,
        
        groups = [
            GroupResponse(
                id=g.id,
                title=g.title,
                description=g.description,
                role=role
            )
            for g, role in user_groups
        ]
)

@router.get("/all-users", response_model=List[UserResponse])
def get_all_users(session: SessionDep, current_user: CurrentUser) -> Any:
    if current_user.is_superuser:
        users = session.exec(select(User)).all()
        
        user_responses = []
        
        for user in users:
            user_groups = session.exec(
                select(Group, UserGroupLink.role).join(UserGroupLink).where(
                    UserGroupLink.user_id == user.id
                )
            ).all()
            
            user_responses.append(
                UserResponse(
                    id=user.id,
                    email=user.email,
                    is_active=user.is_active,
                    is_superuser=user.is_superuser,
                    full_name = user.full_name,
                    
                    groups = [
                        GroupResponse(
                            id=g.id,
                            title=g.title,
                            description=g.description,
                            role=role
                        )
                        for g, role in user_groups
                    ]
                    ))
        return user_responses
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have enough priveleges",
    )

@router.get("/{user_id}", response_model = UserResponse)
def get_one_user(
    session: SessionDep,
    user_id: uuid.UUID,
    current_user:CurrentUser
)-> Any:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required permission as this user"
        )
        
    user = session.exec(
        select(User).where(User.id == user_id)
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    user_groups = session.exec(
        select(Group, UserGroupLink.role).join(UserGroupLink).where(
            UserGroupLink.user_id == user_id
        )).all()
    
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        full_name=user.full_name,
        
        groups = [
            GroupResponse(
                id=g.id,
                title=g.title,
                description=g.description,
                role=role
            )
            for g, role in user_groups
        ]
    )
    
@router.patch(
    "/{user_id}/update-user", 
    dependencies=[Depends(get_active_current_superuser)],
    response_model=UserPublic
)    
def update_user(
    *,
    session:SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate
) -> Any:
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=statu.HTTP_404_NOT_FOUND,
            detail="There is no such user in the system"
        )
    if user_in.email:
        exsiting_user = get_user_by_email(session=session, email=user_in.email)
        if exsiting_user and exsiting_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
    updated_user = edit_user(session=session, db_user=db_user, user_in=user_in)
    return updated_user
        
        
@router.delete(
    "/{user_id}/delete-user",
    dependencies=[Depends(get_active_current_superuser)],
    response_model=Message
)    
def delete_user(
    session:SessionDep, 
    current_user:CurrentUser, 
    user_id: uuid.UUID
) -> Any:    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user == current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusers are not allowed to delete themselves"
        )
    session.exec(
        delete(UserGroupLink).where(
           col(UserGroupLink.user_id)== user_id
        )
    )
    session.delete(user)
    session.commit()
    return Message(
        message = "User deleted successfully"
    )


@router.delete("/me", response_model=Message)
def delete_me(session: SessionDep, current_user: CurrentUser) -> Any:
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusers cannot delete themselves"
        )
        
    session.delete(current_user)
    session.commit()
    return Message(
        message="User deleted successfully"
    )
 

    

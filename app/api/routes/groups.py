import uuid
from app.models import (
    User,
    GroupResponse, 
    GroupRegister, 
    Group,
    UserGroupResponse,
    UserGroupRequest,
    UserGroupLink,
    GroupRequest
)

from app.api.deps import SessionDep, CurrentUser
from fastapi import APIRouter, Depends, HTTPException, status
from app.crud import create_group
from typing import Any, List
from sqlmodel import func, select
from app.utils import require_permission

router = APIRouter()

@router.post("/create-group", response_model=GroupResponse)
def register_group(session: SessionDep, user_in: GroupRegister) -> Any:
    group_create = GroupRegister.model_validate(user_in) 
    new_group = create_group(session=session, group_register=group_create)
    return new_group


@router.get("/all-groups", response_model=List[GroupResponse])
def all_groups(session: SessionDep, current_user:CurrentUser) -> Any:
    if current_user.is_superuser:
        items = session.exec(select(Group)).all()
        return items
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have enough priveleges"
    )
  
@router.post("/{group_id}/add-user", response_model=UserGroupResponse)  
def add_user_to_group(
    session: SessionDep,
    group_id: uuid.UUID,
    current_user: CurrentUser,
    user_in: UserGroupRequest,
)-> Any:
    
    group= session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found "
        )
    user = session.get(User, user_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    existing_user = session.exec(
        select(UserGroupLink).where(
            UserGroupLink.user_id == user_in.user_id,
            UserGroupLink.group_id == group_id
        )
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is already in the group"
        )
        
    require_permission(
        session = session,
        group_id=group_id, 
        current_user=current_user, 
        required_role= "admin"
    )
    
    role = user_in.role
    if current_user.is_superuser:
        role = "admin"
    
    new_user = UserGroupLink(
        user_id = user_in.user_id,
        group_id = group_id,
        role = role   
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return UserGroupResponse(
        user_id=new_user.user_id,
        group_id=new_user.group_id,
        role=new_user.role,
        date_joined=new_user.date_joined.isoformat()
    )
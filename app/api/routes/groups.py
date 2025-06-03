import uuid
from app.models import (
    User,
    GroupResponse, 
    GroupRegister, 
    Group,
    UserGroupResponse,
    UserGroupRequest,
    UserGroupLink,
    GroupRequest,
    GroupUpdate,
    GroupPublic,
    Message
)

from app.api.deps import SessionDep, CurrentUser, get_active_current_superuser
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.crud import create_group, edit_group, get_paginated_sorted_group
from typing import Any, List, Optional
from sqlmodel import func, select, delete, col
from app.utils import(
    require_permission,
    make_creator_admin,
    determine_role, 
    check_user_in_group
)
router = APIRouter()

@router.post("/create-group", response_model=GroupPublic)
def register_group(
    session: SessionDep, 
    user_in: GroupRegister,
    current_user: CurrentUser
) -> Any:
    group_create = GroupRegister.model_validate(user_in) 
    new_group = create_group(session=session, group_register=group_create)
    
    make_creator_admin(
        session,
        new_group.id,
        current_user.id
    )
    return GroupPublic(
        id=new_group.id,
        title=new_group.title,
        description = new_group.description,
        created_at=new_group.created_at,
        created_time=new_group.created_at.strftime("%H:%M:%S")
    )


@router.get("/all-groups", response_model=List[GroupPublic])
def all_groups(
    session: SessionDep, 
    current_user:CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=0),
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    if current_user.is_superuser:
        return get_paginated_sorted_group(
            session, 
            skip, 
            limit, 
            sort_by, 
            sort_order,
            search
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have enough priveleges"
    )
@router.get("/{group_id}/get-group", response_model=GroupPublic)   
def get_a_group(
    session:SessionDep, 
    current_user:CurrentUser,
    group_id: uuid.UUID
) -> Any:
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
        
    is_in_group = check_user_in_group(
        session=session,
        group_id=group_id,
        current_user=current_user
        
    )
    if not is_in_group:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not member of this group"
        )
    group = session.exec(
        select(Group).where(
            Group.id == group_id
        )
    ).first()
    
    return GroupPublic (
        title=group.title,
        description=group.description,
        id=group.id
    )
    
  
@router.patch("/{group_id}/update-group", response_model=GroupPublic)  
def update_group(
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
    group_in: GroupUpdate  
) -> Any:
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    require_permission(
        session=session,
        group_id=group_id,
        current_user=current_user,
        required_role="admin"
    )        
    updated_group = edit_group(session=session,db_group=group, group_in=group_in)
    return updated_group
 
@router.delete(
    "/{group_id}/delete-group", 
    response_model=Message
)   
def delete_group(
    session:SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID
) -> Any:
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
        
    require_permission(
        session=session,
        current_user=current_user,
        group_id=group_id,
        required_role="admin"
    )
        
    session.exec(
        delete(UserGroupLink).where(
            col(UserGroupLink.group_id) == group_id
        )
    )
    session.commit()
    return Message(
        message = "Group deleted successfully"
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
        
    require_permission(
        session = session,
        group_id=group_id, 
        current_user=current_user, 
        required_role= "admin"
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
    
    
    role = determine_role(current_user, user_in.role, user_in.user_id)
    
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

@router.delete("/{group_id}/remove-user", response_model=Message)    
def remove_user_from_group(
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
    user_id: uuid.UUID
) -> Message:
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    require_permission(
        session=session,
        group_id=group_id,
        current_user=current_user,
        required_role="admin"
    )
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    result = session.exec(
        delete(UserGroupLink).where(
            UserGroupLink.user_id == user_id,
            UserGroupLink.group_id == group_id
        )
    )
    user_in_group = result.rowcount
    session.commit() 
    if not user_in_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this group"
        )
     
    return Message(
        message = "User Deleted from the Group Successfully"
    ) 
    
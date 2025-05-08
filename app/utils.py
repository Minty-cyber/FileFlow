import uuid
from app.core.email import EmailSender
from app.core.config import settings
from app.api.deps import SessionDep, CurrentUser
from app.models import Group, GroupRequest, UserGroupLink
from fastapi import HTTPException, status
from sqlmodel import select


def check_user_in_group(
    session: SessionDep,
    group_id: uuid.UUID,
    current_user:CurrentUser
)-> bool:
    if current_user.is_superuser:
        return True
    user_link = session.exec(
        select(UserGroupLink).where(
            UserGroupLink.user_id == current_user.id,
            UserGroupLink.group_id == group_id
        )
    ).first()
    
    return bool(user_link)
    
         
def check_group_permission(
    session: SessionDep,
    group_id: GroupRequest,
    current_user: CurrentUser,
    required_role: str = "admin"   
) -> bool:
    if current_user.is_superuser:
        return True
    
    user_link = session.exec(
        select(UserGroupLink).where(
            UserGroupLink.user_id == current_user.id,
            UserGroupLink.group_id == group_id
        )
    ).first()
    
    if not user_link:
        return False
    
    if required_role == "admin" and user_link.role == "admin":
        return True
    return False

def require_permission(
    session: SessionDep,
    group_id: GroupRequest,
    current_user: CurrentUser,
    required_role: str = "admin"
):
    is_in_group = check_user_in_group(
        session=session,
        group_id=group_id,
        current_user=current_user
        
    )
    if not is_in_group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required permissions here because you are not in the group"
        )
        
    has_permission = check_group_permission(
        session=session,
        group_id=group_id,  
        current_user=current_user,
        required_role=required_role
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required permissions as a member"
        )
        
def determine_role(
    current_user: CurrentUser,
    requested_role: str,
    user_id: uuid.UUID
) -> str:
    if current_user.is_superuser:
        if current_user.id == user_id:
            return "admin"
        return requested_role if requested_role in ["admin", "member"] else "member"
    return "member"
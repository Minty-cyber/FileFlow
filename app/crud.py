from typing import Any, Optional, List
from sqlmodel import Session, select
from app.models import (
    User, 
    UserRegister, 
    UserUpdate,
    GroupRegister, 
    Group,
    GroupUpdate,
    GroupPublic
)
from app.core.security import password_hasher, verify_password


def create_user(*, session: Session, user_register: UserRegister) -> User:
    new_user = User.model_validate(
        user_register, update={
            "hashed_password": password_hasher(user_register.password)
        }
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)   
    return new_user

def get_user_by_email(*, session: Session, email: str) -> User:
    email_object = session.exec(
        select(User).where(User.email == email)
    ).first()
    return email_object

def edit_user(*, session:Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = password_hasher(password)
        extra_data["hashed_password"] = hashed_password
        
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def edit_group(*, session:Session, db_group:Group, group_in:GroupUpdate) -> Any:
    group_data = group_in.model_dump(exclude_unset=True)
    db_group.sqlmodel_update(group_data)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group
    

def authenticate(*, session:Session, email: str, password: str) -> User | None:
    user = get_user_by_email(session=session, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_group(*, session: Session, group_register: GroupRegister) -> Group:
    new_group = Group.model_validate(group_register)
    session.add(new_group)
    session.commit()
    session.refresh(new_group)
    return new_group
    
def get_paginated_sorted_group(
    session : Session,
    skip: int = 0,
    limit: int = 0,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None
    
) -> list[Group]:
    statement = select(Group)
    
    sort_attributes = ["title", "description", "created_at"]
    sort_attribute_name = "created_at"
    
    if sort_by and sort_by in sort_attributes:
        sort_attribute_name = sort_by
        
    sort_column = getattr(Group, sort_attribute_name)
    
    if sort_order and sort_order.lower() == "desc":
        statement = statement.order_by(sort_column.desc())
        
    else:
        statement = statement.order_by(sort_column.asc())
        
    statement = statement.offset(skip).limit(limit)
    groups = session.exec(statement).all()
    return groups
    
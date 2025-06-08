from typing import Any, Optional, List
from sqlmodel import Session, select
from app.models import (
    User, 
    UserRegister, 
    UserUpdate,
    GroupRegister, 
    Group,
    GroupUpdate,
    GroupPublic,
    ExceptionLog
)
from app.core.security import password_hasher, verify_password
from app.handlers.crud_handler import CRUDRepository

user_handler = CRUDRepository[User](User)
group_handler = CRUDRepository[Group](Group)


def create_user(*, session: Session, user_register: UserRegister) -> User:
    extra_data = {"hashed_password": password_hasher(user_register.password)}
    return user_handler.create(session=session, data=user_register, extra_data=extra_data)


def get_user_by_email(*, session: Session, email: str) -> User:
    return user_handler.get_by_field(session=session, field="email", value=email)


def edit_user(*, session: Session, db_user: User, user_in: UserUpdate) -> User:
    extra_data = {}
    if user_in.password:
        extra_data["hashed_password"] = password_hasher(user_in.password)
    return user_handler.update(session=session, db_instance=db_user, update_data=user_in, extra_data=extra_data)


def edit_group(*, session: Session, db_group: Group, group_in: GroupUpdate) -> Any:
    return group_handler.update(session=session, db_instance=db_group, update_data=group_in)

def authenticate(*, session: Session, email: str, password: str) -> User | None:
    user = user_handler.get_by_field(session=session, field=email, value=email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
   

def create_group(*, session: Session, group_register: GroupRegister) -> Group:
    return group_handler.create(session=session, data=group_register)
    
def get_paginated_sorted_group(
    session : Session,
    skip: int = 0,
    limit: int = 5,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None
    
) -> list[Group]:
    statement = select(Group)
    
    sort_attributes = ["title", "description", "created_at"]
    sort_attribute_name = "created_at"
    
    sort_attribute_name = sort_by if sort_by in sort_attributes else "created_at"
    sort_column = getattr(Group, sort_attribute_name)
    
    statement = statement.order_by(
        sort_column.desc() if sort_order and sort_order.lower() == "desc" else sort_column.asc()
    )   
    statement = statement.offset(skip).limit(limit)
    return session.exec(statement).all()

def get_paginated_sorted_user(
    session: Session,
    skip: int = 0,
    limit: int = 5,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    search: Optional[str] = None
) -> list[User]:
    statement = select(User)
    
    if search:
        search = f"%{search}%"
        statement = statement.where(
            (User.email.ilike(search)) | 
            (User.full_name.ilike(search))
        )
    
    sort_attributes = ["email", "full_name", "is_active"]
    sort_attribute_name = sort_by if sort_by in sort_attributes else "email"
    
    sort_column = getattr(User, sort_attribute_name)
    
    statement = statement.order_by(
        sort_column.desc() if sort_order and sort_order.lower() == "desc" else sort_column.asc()
    )   
    statement = statement.offset(skip).limit(limit)
    return session.exec(statement).all()

def get_paginated_sorted_group(
    session : Session,
    skip: int = 0,
    limit: int = 5,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    search: Optional[str] = None
) -> list[Group]:
    statement = select(Group)
    
    if search:
        search = f"%{search}%"
        statement = statement.where(
            (Group.title.ilike(search)) | 
            (Group.description.ilike(search))
        )
    
    sort_attributes = ["title", "description", "created_at"]
    sort_attribute_name = "created_at"
    
    sort_attribute_name = sort_by if sort_by in sort_attributes else "created_at"
    sort_column = getattr(Group, sort_attribute_name)
    
    statement = statement.order_by(
        sort_column.desc() if sort_order and sort_order.lower() == "desc" else sort_column.asc()
    )   
    statement = statement.offset(skip).limit(limit)
    return session.exec(statement).all()

def get_paginated_sorted_error_logs(
    session: Session,
    skip: int = 0,
    limit: int = 5,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    search: Optional[str] = None
) -> list[User]:
    statement = select(ExceptionLog)
    
    if search:
        search = f"%{search}%"
        statement = statement.where(
            (ExceptionLog.error_message.ilike(search)) | 
            (ExceptionLog.error_type.ilike(search)) |
            (ExceptionLog.username.ilike(search))
        )
    
    sort_attributes = ["username", "error_message", "error_type", "timestamp"]
    sort_attribute_name = sort_by if sort_by in sort_attributes else "timestamp"
    sort_column = getattr(ExceptionLog, sort_attribute_name)
    
    statement = statement.order_by(
        sort_column.desc() if sort_order and sort_order.lower() == "desc" else sort_column.asc()
    )   
    statement = statement.offset(skip).limit(limit)
    return session.exec(statement).all()

    
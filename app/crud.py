from typing import Any
from sqlmodel import Session, select
from app.models import (
    User, 
    UserRegister, 
    UserUpdate,
    GroupRegister, 
    Group
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
    
    
    
from typing import Any
from sqlmodel import Session, select
from app.models import User, UserRegister
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

def authenticate(*, session:Session, email: str, password: str) -> User | None:
    user = get_user_by_email(session=session, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
    

    
    
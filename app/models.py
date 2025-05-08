import uuid
from typing import Annotated, Optional, List, Literal
from fastapi import Form
from pydantic import EmailStr, field_validator
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class UserGroupLink(SQLModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True, ondelete="CASCADE")
    group_id: uuid.UUID = Field(foreign_key="group.id", primary_key=True, ondelete="CASCADE")
    role: str = Field(default="member")
    date_joined: datetime = Field(default_factory=datetime.utcnow)
    user: Optional["User"] = Relationship(back_populates="group_links")
    group: Optional["Group"] = Relationship(back_populates="user_links")

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = Field(default=None, max_length=255)

class GroupBase(SQLModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    group_links: List["UserGroupLink"] = Relationship(back_populates="user")
    groups: List["Group"] = Relationship(
        back_populates="users", 
        link_model=UserGroupLink, 
        sa_relationship_kwargs={"viewonly": True})

class Group(GroupBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_links: List["UserGroupLink"] = Relationship(back_populates="group")
    users: List[User] = Relationship(
        back_populates="groups", 
        link_model=UserGroupLink, 
        sa_relationship_kwargs={"viewonly": True})

class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=40)
    
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)

class GroupRegister(GroupBase):
    pass

class UserResponse(UserBase):
    id: uuid.UUID
    groups: List["GroupResponse"] = []
    
class UserPublic(UserBase):
    id: uuid.UUID

class GroupResponse(GroupBase):
    id: uuid.UUID
    role: str

class GroupPublic(GroupBase):
    id:uuid.UUID
    
class GroupUpdate(GroupBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    
class GroupRequest(SQLModel):
    group_id: uuid.UUID
    
class UserGroupRequest(SQLModel):
    user_id: uuid.UUID
    role: Literal ["admin", "member"] = "member"
    
class UserGroupResponse(SQLModel):
    user_id: uuid.UUID
    group_id: uuid.UUID
    role: str
    date_joined: str 

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

class TokenInfo(SQLModel):
    sub: Optional[str] = None

class OAuth2PasswordRequestFormEmail(SQLModel):
    email: str = Field(..., description="The user's email address")
    password: str = Field(..., description="The user's password")

    @classmethod
    def as_form(
        cls,
        email: str = Form(...),
        password: str = Form(...)
    ) -> 'OAuth2PasswordRequestFormEmail':
        return cls(email=email, password=password)
    
class Message(SQLModel):
    message: str
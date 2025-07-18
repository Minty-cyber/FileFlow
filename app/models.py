import uuid
from typing import Annotated, Optional, List, Literal
from fastapi import Form
from pydantic import EmailStr, field_validator, BaseModel
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone

from beanie import Document, Indexed


class UserGroupLink(SQLModel, table=True):
    user_id: uuid.UUID = Field(
        foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    group_id: uuid.UUID = Field(
        foreign_key="group.id", primary_key=True, ondelete="CASCADE"
    )
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
        sa_relationship_kwargs={"viewonly": True},
    )


class Group(GroupBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_links: List["UserGroupLink"] = Relationship(back_populates="group")
    users: List[User] = Relationship(
        back_populates="groups",
        link_model=UserGroupLink,
        sa_relationship_kwargs={"viewonly": True},
    )


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
    id: uuid.UUID


class GroupUpdate(GroupBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)


class GroupRequest(SQLModel):
    group_id: uuid.UUID


class UserGroupRequest(SQLModel):
    user_id: uuid.UUID
    role: Literal["admin", "member"] = "member"


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
        cls, email: str = Form(...), password: str = Form(...)
    ) -> "OAuth2PasswordRequestFormEmail":
        return cls(email=email, password=password)


class Message(SQLModel):
    message: str


class ExceptionLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: Optional[str] = Field(default=None, index=True)
    error_type: Optional[str] = Field(default=None, index=True)
    error_message: str
    stack_trace: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = Field(default=None)
    method: Optional[str] = Field(default=None)
    client_ip: Optional[str] = Field(default=None)


class Room(Document):
    participants: Annotated[List[str], Indexed()]
    room_type: str = "private"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "rooms"
        indexes = [[("participants", 1)]]


class Message(Document):
    room_id: str
    sender_id: Annotated[str, Indexed()]
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "messages"
        idexes = [[("room_id", 1), ("timestamp", 1)]]


class ChatRoomRequest(BaseModel):
    participants: List[str]
    room_type: str = "private"


class ChatRoomResponse(BaseModel):
    room_id: str
    participants: List[str]
    room_type: str
    created_at: datetime


# For testing purposes
class BasePost(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = []


class Post(Document):
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    user_id: uuid.UUID
    user_email: str
    published: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    class Settings:
        name = "all"


class PostResponse(BasePost):
    id: str
    user_id: uuid.UUID
    user_email: str
    published: bool
    created_at: datetime
    updated_at: Optional[datetime]

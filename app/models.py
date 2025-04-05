import uuid
from pydantic import EmailStr
from fastapi import Form
from sqlmodel import Field, Relationship, SQLModel

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    
        
class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=40)
    
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    
class UserResponse(UserBase):
    id: uuid.UUID
    
class Token(SQLModel):
    access_token : str
    token_type: str ="bearer"
    
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
    
from typing import Any
from datetime import timedelta, timezone, datetime
from passlib.context import CryptContext
from app.core.config import settings
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, encrypted_password: str) -> bool:
    return pwd_context.verify(plain_password, encrypted_password)

def password_hasher(password: str) -> str:
    encrypted_password  = pwd_context.hash(password)
    return encrypted_password

def generate_otp() -> str:
    generated_otp = totp.now()
 
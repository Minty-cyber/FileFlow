from fastapi.testclient import TestClient
from sqlmodel import Session

from app.crud import create_user, get_user_by_email
from app.core.config import settings
from app.models import User,UserRegister
from app.tests.utils.core import random_email, random_string
from app.core.email import EmailSender

def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]: 
    user_data = {
        "email" : email,
        "password" : password
    }
    r = client.post(f"{settings.API_V1_STR}/users/login", data=user_data)
    print(user_data)
    response = r.json()
    print(response)
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers
    
def create_random_user(db: Session) -> User:
    email = random_email()
    password = random_string()
    user_in = UserRegister(email=email, password=password)
    user = create_user(session=db, user_register=user_in)
    return user

def authentication_token_from_email(
    *, 
    client: TestClient, 
    email: str,
    password: str,
    db: Session
) -> dict[str, str]:
    user = get_user_by_email(session=db, email=email)
    if not user:
        user_in = UserRegister(email=email, password=password)
        user = create_user(session=db, user_register=user_in)
        
        
    return user_authentication_headers(
        client=client,
        email=email,
        password=password
    )

  

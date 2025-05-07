from fastapi.encoders import jsonable_encoder
from app.models import User, UserRegister
from app.crud import create_user, authenticate
from app.tests.utils.core import random_email, random_string
from sqlmodel import Session
from app.core.config import settings


def test_create_user(database: Session):
    email = random_email()
    password = random_string()
    full_name = settings.TEST_USER
    user_in = UserRegister(email=email, password=password, full_name=full_name)
    user = create_user(session=database, user_register=user_in)
    assert user.email == email
    assert user.full_name == full_name
    assert hasattr(user, "hashed_password")
    
def test_authenticate_user(database: Session):
    email = random_email()
    password = random_string()
    full_name = settings.TEST_USER
    user_in = UserRegister(email=email, password=password, full_name=full_name)
    user = create_user(session=database, user_register=user_in)
    auth_user = authenticate(session=database, email=email, password=password)
    assert auth_user
    assert user.email == auth_user.email


def test_not_authenticate_user(database: Session):
    email = random_email()
    password = random_string()
    user = authenticate(session=database, email=email, password=password)
    assert user is None
    
def test_get_user(database: Session):
    email = random_email()
    password = random_string()
    full_name = settings.TEST_USER
    user_in = UserRegister(email=email, password=password, full_name=full_name)
    user = create_user(session=database, user_register=user_in)
    user_get = database.get(User, user.id)
    assert user_get
    assert user.email == user_get.email
    assert jsonable_encoder(user) == jsonable_encoder(user_get)
    
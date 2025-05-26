import pytest
from collections.abc import Generator
from fastapi.testclient import TestClient
from sqlmodel import Session, delete
from app.core.config import settings
from app.main import app
from app.models import User
from app.core.database import engine, populate_database_users
from app.tests.utils.core import get_superuser_token_headers
from app.tests.utils.user import authentication_token_from_email
from app.api.deps import get_db

@pytest.fixture(scope="function")
def database():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    app.dependency_overrides[get_db] = lambda: session
    
    yield session
    
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(database) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function") 
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)

@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, database: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, password=settings.EMAIL_TEST_USER_PASSWORD, db=database
    )
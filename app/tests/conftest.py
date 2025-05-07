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


@pytest.fixture(scope="session", autouse=True)
def database() -> Generator[Session, None, None]:
    with Session(engine) as session:
        populate_database_users(session)
        yield session
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, database: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, password=settings.EMAIL_TEST_USER_PASSWORD, db=database
    )

from fastapi.testclient import TestClient
from app.core.config import settings
from app.tests.utils.user import random_email, random_string





def test_get_access_token(client: TestClient):
    login_data = {
        "email": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD
    }
    r = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]
    
def test_incorrect_email(client: TestClient):
    login_data = {
        "email" : random_email(),
        "password": settings.FIRST_SUPERUSER_PASSWORD
    }
    r = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    response = r.json()
    assert r.status_code == 400
    assert response["detail"] == "Incorrect email or password"
    
def test_incorrect_password(client: TestClient):
    password = random_string()
    login_data = {
        "email": settings.FIRST_SUPERUSER,
        "password" : random_string()
    }
    r = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    response = r.json()
    assert r.status_code == 400
    assert response["detail"] == "Incorrect email or password"
    
def test_use_access_token(client: TestClient,
    superuser_token_headers: dict[str, str]):
    r = client.post(
        f"{settings.API_V1_STR}/users/login/test-token",
        headers = superuser_token_headers
    )
    response = r.json()
    assert r.status_code == 200
    assert "email" in response
    
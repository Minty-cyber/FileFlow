from fastapi.testclient import TestClient
from app.core.config import settings


def test_get_superuser_profile(client: TestClient, 
    superuser_token_headers: dict[str, str]) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    user_profile = r.json()
    assert user_profile
    assert user_profile["is_active"] is True
    assert user_profile["is_superuser"] is True
    assert user_profile["email"] == settings.FIRST_SUPERUSER

def test_get_normal_user(client: TestClient, 
    normal_user_token_headers: dict[str, str]) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers) 
    user_profile =r.json()
    print(user_profile)
    assert user_profile
    assert user_profile["is_active"] is True
    assert user_profile["is_superuser"] is False
    assert user_profile["email"] == settings.EMAIL_TEST_USER
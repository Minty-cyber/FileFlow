import random 
import string 
from fastapi.testclient import TestClient
from app.core.config import settings



def random_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))

def random_email() -> str:
    return f"{random_string()}@{random_string()}.com"

def get_superuser_token_headers(auth_client: TestClient) -> dict[str, str]:
    login_data = {
        "email": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD
    }
    r = auth_client.post(
        f"{settings.API_V1_STR}/users/login",
        data=login_data, 
    )
    tokens = r.json()
    access_token = tokens["access_token"]
    headers={"Authorization": f"Bearer {access_token}"}
    return headers
    
    
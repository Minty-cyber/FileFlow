import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.config import settings
from app.tests.utils.group import create_random_group

def test_create_group(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    database: Session
) -> None:
    data = {
        "title": "Test Group",
        "description": "This is a test group"
    }
    response = client.post(
        f"{settings.API_V1_STR}/groups/create-group/",
        headers=superuser_token_headers,
        json=data
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] is not None
    assert content["created_at"] is not None
    
def test_read_group(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    database: Session
) -> None:
    group = create_random_group(database)
    response = client.get(
        f"{settings.API_V1_STR}/groups/{group.id}/get-group",
        headers=superuser_token_headers,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == group.title
    assert content["description"] == group.description
    assert content["id"] == str(group.id)
    assert content["created_at"] is not None
    
def test_all_groups(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    database: Session
) -> None:
    first_group = create_random_group(database)
    second_group = create_random_group(database)
    response = client.get(
        f"{settings.API_V1_STR}/groups/all-groups",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    
    assert isinstance(content, list)
    assert len(content) >= 2
    
def test_read_all_groups_less_permission(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    database: Session
) -> None:
    first_group = create_random_group(database)
    second_group = create_random_group(database)
    response = client.get(
        f"{settings.API_V1_STR}/groups/all-groups",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "You do not have enough priveleges"
    
    
def test_read_group_not_found(
    client:TestClient,
    superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/groups/{uuid.uuid4()}/get-group",
        headers=superuser_token_headers,
    )
    
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Group not found"
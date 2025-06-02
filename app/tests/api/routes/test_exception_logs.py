import uuid
from app.models import ExceptionLog
from datetime import datetime, timezone
from fastapi import status
from app.core.config import settings
from sqlmodel import select
from app.tests.utils.log import create_dummy_logs, create_random_log

BASE_URL = f"{settings.API_V1_STR}/logs"

def test_delete_all_error_logs(client, database, superuser_token_headers):
    # Add two logs
    create_dummy_logs(database, num_logs=2)
    response = client.delete(f"{BASE_URL}/error-logs", headers=superuser_token_headers)
    assert response.status_code == status.HTTP_200_OK

    # Confirm deletion
    statement = select(ExceptionLog)
    logs = database.exec(statement).all()
    assert len(logs) == 0


def test_delete_specific_error_log(client, database, superuser_token_headers):
    log = create_random_log(database) 
    log_id = str(log.id)
    response = client.delete(f"{BASE_URL}/error-logs/{log_id}", headers=superuser_token_headers)
    assert response.status_code == status.HTTP_200_OK

    # Confirm deletion
    log = database.get(ExceptionLog, log_id)
    assert log is None

def test_delete_nonexistent_log(client, superuser_token_headers):
    fake_id = str(uuid.uuid4())
    response = client.delete(f"{BASE_URL}/error-logs/{fake_id}", headers=superuser_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_only_active_superuser_can_delete_all_logs(client, database, normal_user_token_headers):
    # Add two logs
    create_dummy_logs(database, num_logs=2)
    response = client.delete(f"{BASE_URL}/error-logs", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Confirm deletion did not occur
    statement = select(ExceptionLog)
    logs = database.exec(statement).all()
    assert len(logs) != 0


def test_only_active_superuser_can_delete_specific_logs(client, database, normal_user_token_headers):
    log = create_random_log(database)
    log_id = str(log.id)
    response = client.delete(f"{BASE_URL}/error-logs/{log_id}", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Confirm deletion did not occur
    log = database.get(ExceptionLog, log_id)   
    assert log is not None

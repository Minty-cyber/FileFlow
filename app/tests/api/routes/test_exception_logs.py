import uuid
from app.models import ExceptionLog
from datetime import datetime, timezone
from fastapi import status
from app.core.config import settings
from sqlmodel import select

BASE_URL = f"{settings.API_V1_STR}/logs"

def test_delete_all_error_logs(client, database, superuser_token_headers):
    # Add two logs
    for i in range(2):
        log = ExceptionLog(
            id=uuid.uuid4(),
            username=f"user{i}",
            error_type="TypeError",
            error_message=f"Error {i}",
            stack_trace="Traceback\n...",
            timestamp=datetime.now(timezone.utc),
            path="/test",
            method="POST",
            client_ip="127.0.0.1"
        )
        database.add(log)
    database.commit()

    response = client.delete(f"{BASE_URL}/error-logs", headers=superuser_token_headers)
    assert response.status_code == status.HTTP_200_OK

    # Confirm deletion
    statement = select(ExceptionLog)
    logs = database.exec(statement).all()
    assert len(logs) == 0
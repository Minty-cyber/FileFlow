from sqlmodel import Session
from app.models import ExceptionLog
from datetime import datetime, timezone
import uuid

def create_dummy_logs(database: Session, num_logs: int) -> None:
    """
     Create dummy exception logs in the database.
    """
    for i in range(num_logs):
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
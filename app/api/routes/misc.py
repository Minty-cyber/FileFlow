from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List
from sqlmodel import select, Session
from app.models import ExceptionLog
from app.api.deps import SessionDep

router = APIRouter()

@router.get("/error-logs", response_model=List[Any])
def get_error_logs(session: SessionDep) -> Any:
    """
    Returns all exception logs as a list of JSON objects.
    """
    logs = session.exec(select(ExceptionLog)).all()
    return [log.model_dump() for log in logs]

# Add more miscellaneous routes here as needed.
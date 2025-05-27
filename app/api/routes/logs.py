from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List
from sqlmodel import select, Session
from app.models import ExceptionLog
from app.api.deps import SessionDep
from app.api.responses import ExceptionLogResponse

router = APIRouter()

@router.get("/error-logs", response_model=List[ExceptionLogResponse])
def get_error_logs(session: SessionDep) -> Any:
    """
    Returns all exception logs as a list of JSON objects.
    """
    logs = session.exec(select(ExceptionLog)).all()
    result = []
    for log in logs:
        log = log.model_dump()
        log['stack_trace'] = log['stack_trace'].splitlines() if log['stack_trace'] else []
        result.append(log)
    return result


# Add more miscellaneous routes here as needed.
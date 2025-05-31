from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any, List
from sqlmodel import select, Session
from app.models import ExceptionLog
from app.api.deps import SessionDep
from app.decorators import superuser_only 

router = APIRouter()

@router.get("/error-logs", response_model=List[ExceptionLog])
@superuser_only
async def get_error_logs(request:Request, session: SessionDep, user=None) -> Any:
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


@router.delete("/error-logs")
@superuser_only
def delete_all_error_logs(session: SessionDep, user=None):
    """
    Deletes all exception logs from the database.
    """
    logs = session.exec(select(ExceptionLog)).all()
    for log in logs: 
        session.delete(log)
    session.commit()
    return {'message': 'All logs deleted successfully'}

@router.delete("/error-logs/{log_id}")
@superuser_only
def delete_error_log(log_id: str, session: SessionDep, user=None):
    """
    Deletes a specific exception log by its ID.
    """
    log = session.get(ExceptionLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    session.delete(log)
    session.commit()
    return {'message': 'Log deleted successfully'}
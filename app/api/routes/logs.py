from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Any, List, Optional
from sqlmodel import select
from app.models import ExceptionLog
from app.api.deps import SessionDep, get_active_current_superuser
from app.crud import get_paginated_sorted_error_logs

router = APIRouter()

@router.get(
    "/error-logs",
    dependencies=[Depends(get_active_current_superuser)], 
    response_model=List[ExceptionLog]
)
async def get_error_logs(
    session: SessionDep,
    skip: int = Query(0, ge=0) ,
    limit: int = Query(5, ge=1),
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    """
    Returns all exception logs as a list of JSON objects.
    """
    logs = get_paginated_sorted_error_logs(
        session,
        skip,
        limit,
        sort_by,
        sort_order,
        search
    )
    result = []
    for log in logs:
        log = log.model_dump()
        log['stack_trace'] = log['stack_trace'].splitlines() if log['stack_trace'] else []
        result.append(log)
    return result


@router.delete(
    "/error-logs",
    dependencies=[Depends(get_active_current_superuser)]
)
async def delete_all_error_logs(session: SessionDep):
    """
    Deletes all exception logs from the database.
    """
    logs = session.exec(select(ExceptionLog)).all()
    for log in logs: 
        session.delete(log)
    session.commit()
    return {'message': 'All logs deleted successfully'}

@router.delete(
    "/error-logs/{log_id}",
    dependencies=[Depends(get_active_current_superuser)]
)
async def delete_error_log(session: SessionDep, log_id: str):
    """
    Deletes a specific exception log by its ID.
    """
    log = session.get(ExceptionLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    session.delete(log)
    session.commit()
    return {'message': 'Log deleted successfully'}
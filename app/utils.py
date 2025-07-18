import uuid
# from app.core.email import EmailSender
from app.core.config import settings
from app.api.deps import SessionDep, CurrentUser
from app.models import (
    User,
    Group,
    GroupRequest,
    Room,
    UserGroupLink,
    ExceptionLog,
    ChatRoomRequest,
    ChatRoomResponse,
)
from fastapi import HTTPException, status, Request, WebSocket
from sqlmodel import select, Session

import traceback
from app.core.database import engine


def check_user_in_group(
    session: SessionDep, group_id: uuid.UUID, current_user: CurrentUser
) -> bool:
    if current_user.is_superuser:
        return True
    user_link = session.exec(
        select(UserGroupLink).where(
            UserGroupLink.user_id == current_user.id, UserGroupLink.group_id == group_id
        )
    ).first()

    return bool(user_link)


def make_creator_admin(session: SessionDep, group_id: uuid.UUID, creator_id: uuid.UUID):
    new_admin = UserGroupLink(user_id=creator_id, group_id=group_id, role="admin")
    session.add(new_admin)
    session.commit()


def check_group_permission(
    session: SessionDep,
    group_id: GroupRequest,
    current_user: CurrentUser,
    required_role: str = "admin",
) -> bool:
    if current_user.is_superuser:
        return True

    user_link = session.exec(
        select(UserGroupLink).where(
            UserGroupLink.user_id == current_user.id, UserGroupLink.group_id == group_id
        )
    ).first()

    if not user_link:
        return False

    if required_role == "admin" and user_link.role == "admin":
        return True
    return False


def require_permission(
    session: SessionDep,
    group_id: GroupRequest,
    current_user: CurrentUser,
    required_role: str = "admin",
):
    is_in_group = check_user_in_group(
        session=session, group_id=group_id, current_user=current_user
    )
    if not is_in_group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required permissions here because you are not in the group",
        )

    has_permission = check_group_permission(
        session=session,
        group_id=group_id,
        current_user=current_user,
        required_role=required_role,
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required permissions as a member",
        )


def determine_role(
    current_user: CurrentUser, requested_role: str, user_id: uuid.UUID
) -> str:
    if current_user.is_superuser:
        if current_user.id == user_id:
            return "admin"
        return requested_role if requested_role in ["admin", "member"] else "member"
    return "member"


def log_exception_to_db(
    session: Session, exc: Exception, request: Request, username: str = None
):
    stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    log = ExceptionLog(
        username=username,
        error_type=type(exc).__name__,
        error_message=str(exc),
        stack_trace=stack,
        path=str(request.url),
        method=request.method,
        client_ip=request.client.host if request.client else None,
    )
    session.add(log)
    session.commit()

async def room_creation_validation(
    current_user: CurrentUser, 
    session: SessionDep, 
    user_in: ChatRoomRequest
) -> None:
    current_user_id = str(current_user.id)
    participants = request.participants
    room_type = ["private", "group"]
    if request.room_type not in room_type:
        raise HTTPException(
            status_code=400, detail=f"room_type must be one of: {', '.join(valid_types)}",
        )
    if len(participants) < 2:
        raise HTTPException(
            status_code=400, detail="At least two participants are required"
        )
    for participant_id in participants:
        try:
            uuid.UUID(participant_id)
        except ValueError:
            raise HTTPException(
                 status_code=400, detail="Invalid ID. ID must be a UUID"
            )
    for participant_id in participants:
        participant_uuid = uuid.UUID(participant_id)
        user = session.exec(select(User).where(User.id == participant_uuid)).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with id {participant_id} not found in the database",
            )
    if current_user_id not in participants:
        raise HTTPException(
            status_code=403, detail="You must be a participant in the room to create it"
        )

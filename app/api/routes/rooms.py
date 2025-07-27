from app.models import (
    PrivateChatRoomRequest,
    PrivateChatRoomResponse,
    Room,
    User,
    Group,
    UserGroupLink,
    GroupChatRoomRequest,
    GroupChatRoomResponse,
)
from typing import Any
from fastapi import APIRouter, HTTPException, WebSocket
from app.utils import room_creation_validation
from app.api.deps import CurrentUser, SessionDep
from sqlmodel import select

from bson import ObjectId

router = APIRouter()


@router.post("/private_room", response_model=PrivateChatRoomResponse)
async def create_private_room(
    current_user: CurrentUser, session: SessionDep, user_in: PrivateChatRoomRequest
) -> Any:
    await room_creation_validation(
        current_user=current_user, session=session, user_in=user_in
    )

    sorted_participants = sorted(user_in.participants)
    query = {
        "participants": {
            "$all": sorted_participants,
            "$size": len(sorted_participants),
        },
        "room_type": user_in.room_type,
    }

    if user_in.room_type == "group":
        query["room_name"] = user_in.room_name

    existing_room = await Room.find_one(query)

    if user_in.room_type == "private" and existing_room:
        return ChatRoomResponse(
            room_id=str(existing_room.id),
            participants=existing_room.participants,
            room_type=existing_room.room_type,
            room_name=existing_room.room_name,
            created_at=existing_room.created_at,
        )

    room_params = {"participants": sorted_participants, "room_type": user_in.room_type}

    if user_in.room_type == "group":
        room_params["room_name"] = user_in.room_name

    new_room = Room(**room_params)
    await new_room.insert()
    return ChatRoomResponse(
        room_id=str(new_room.id),
        participants=new_room.participants,
        room_type=new_room.room_type,
        room_name=new_room.room_name,
        created_at=new_room.created_at,
    )

@router.post("/group_room", response_model=GroupChatRoomResponse)
async def create_group_room(
    user_in: GroupChatRoomRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    group = session.get(Group, user_in.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members_query = (
        select(User.id).join(UserGroupLink).where(UserGroupLink.group_id == group.id)
    )
    group_members = session.exec(members_query).all()

    ## Simply put, you must be part of the group to be able to send messages in the group
    if str(current_user.id) not in [str(member) for member in group_members]:
        raise HTTPException(
            status_code=403,
            detail="You must be a member of the group to create a chat room",
        )

    participants = [str(member) for member in group_members]
    
    existing_room_query = {
        "group_id": str(group.id),
        "room_type": "group"
    }
    existing_room = await Room.find_one(existing_room_query)
    
    if existing_room:
        return GroupChatRoomResponse(
        room_id=str(existing_room.id),
        group_id=str(group.id),
        room_name=existing_room.room_name,
        participants=existing_room.participants,
        created_at=existing_room.created_at,
    )
        

    new_room = Room(
        participants=participants,
        room_type="group",
        room_name=user_in.room_name or group.title,
        group_id=str(group.id),
        created_by=str(current_user.id),
    )
    await new_room.insert()

    return GroupChatRoomResponse(
        room_id=str(new_room.id),
        group_id=str(group.id),
        room_name=new_room.room_name,
        participants=new_room.participants,
        created_at=new_room.created_at,
    )





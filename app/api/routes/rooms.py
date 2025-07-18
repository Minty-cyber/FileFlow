from app.models import ChatRoomRequest, ChatRoomResponse, Room, User
from typing import Any
from fastapi import APIRouter, HTTPException, WebSocket
from app.utils import room_creation_validation
from app.api.deps import CurrentUser, SessionDep

router = APIRouter()


@router.post("/create-room", response_model=ChatRoomResponse)
async def create_room(
    current_user: CurrentUser, session: SessionDep, request: ChatRoomRequest
) -> Any:
    await room_creation_validation(current_user=current_user, session=session, request=request)

    sorted_participants = sorted(request.participants)
    existing_room = await Room.find_one(
        {
            "participants": {
                "$all": sorted_participants,
                "$size": len(sorted_participants),
            },
            "room_type": request.room_type,
        }
    )

    if existing_room:
        return ChatRoomResponse(
            room_id=str(existing_room.id),
            participants=existing_room.participants,
            room_type=existing_room.room_type,
            created_at=existing_room.created_at,
        )

    new_room = Room(participants=sorted_participants, room_type=request.room_type)
    await new_room.insert()
    return ChatRoomResponse(
        room_id=str(new_room.id),
        participants=new_room.participants,
        room_type=new_room.room_type,
        created_at=new_room.created_at,
    )

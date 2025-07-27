import json
import logging
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.core.chat_config import manager
from typing import List, Any
from app.api.deps import authenticate_ws
from app.models import User, Room, Message
from app.api.deps import SessionDep

from bson import ObjectId

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_private_message(
    user: User, room: Room, message_content: str, ws: WebSocket
) -> Any:
    sender_id = str(user.id)
    sender_email = user.email
    sender_name = user.full_name
    # Convert ObjectId to string for the Message model
    message = Message(room_id=str(room.id), sender_id=sender_id, message=message_content)
    await message.insert()

    for participant in room.participants:
        if participant != sender_id:
            await manager.broadcast_to_user(
                json.dumps(
                    {
                        "room_id": str(room.id),
                        "sender_id": sender_id,
                        "sender_email": sender_email,
                        "sender_name": sender_name,
                        "message": message_content,
                        "timestamp": message.timestamp.isoformat(),
                    }
                ),
                participant,
            )
    await manager.send_personal_message(
        json.dumps(
            {
                "status": "sent",
                "room_id": str(room.id),
                "message": message_content,
                "timestamp": message.timestamp.isoformat(),
            }
        ),
        ws,
    )


async def handle_group_message(
    user: User, room: Room, message_content: str, ws: WebSocket
) -> Any:
    sender_id = str(user.id)
    sender_email = user.email
    sender_name = user.full_name

    message = Message(room_id=str(room.id), sender_id=sender_id, message=message_content)
    await message.insert()

    logger.info(f"Group message created for room {room.id}")
    logger.info(f"Room participants: {room.participants}")
    logger.info(f"Sender ID: {sender_id}")
   
    # Broadcast to all participants except sender
    broadcast_count = 0
    for participant in room.participants:
        logger.info(f"Checking participant: {participant} (type: {type(participant)})") ##Check the type of the participant
        if participant != sender_id:
            logger.info(f"Broadcasting to participant: {participant}")
            # Check if manager has this user's connection
            has_connection = participant in manager.user_connections
            connection_count = manager.get_user_connection_count(participant)
            logger.info(f"Manager has connection for {participant}: {has_connection}")
            logger.info(f"Connection count for {participant}: {connection_count}")
            logger.info(f"All connected users: {manager.get_connected_users()}")
            
            try:
                message_payload = json.dumps({
                    "type": "group_message",
                    "room_id": str(room.id),
                    "room_name": room.room_name,
                    "sender_id": sender_id,
                    "sender_email": sender_email,
                    "sender_name": sender_name,
                    "message": message_content,
                    "timestamp": message.timestamp.isoformat(),
                })
                logger.info(f"Message payload: {message_payload}")
                
                await manager.broadcast_to_user(message_payload, participant)
                broadcast_count += 1
                logger.info(f"Successfully broadcast to {participant}")
            except Exception as e:
                logger.error(f"Failed to broadcast to {participant}: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
        else:
            logger.info(f"Skipping sender: {participant}")
    
    logger.info(f"Total broadcasts sent: {broadcast_count}")
    await manager.send_personal_message(
        json.dumps(
            {
                "status": "sent",
                "type": "group_message",
                "room_id": str(room.id),
                "room_name": room.room_name,
                "message": message_content,
                "timestamp": message.timestamp.isoformat(),
            }
        ),
        ws,
    )


@router.websocket("/ws")
async def chat(websocket: WebSocket, session: SessionDep):
    user = await authenticate_ws(websocket, session)
    sender_id = str(user.id)
    logger.info(f"Sender id: {sender_id}")
    sender_email = user.email
    sender_name = user.full_name
    if not user:
        return  # WebSocket already closed by authenticate_ws

    await manager.connect(websocket, user)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"WS received text: {data}")
            try:
                message_data = json.loads(data)
                logger.info(f"Load Full Message data: {message_data}")
                room_id = message_data.get("room_id")
                logger.info(
                    f"Logging the room_id being sent:{room_id} with type: {type(room_id)}"
                )
                message_content = message_data.get("message")
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"error": "Invalid JSON Format"}), websocket
                )
                continue
            room = await Room.find_one({"_id": ObjectId(room_id)})
            logger.info(f"Room found: {room}")
            if room:
                logger.info(f"Room type: {room.room_type}")
                logger.info(f"Room participants: {room.participants}")
                logger.info(f"Sender in participants: {sender_id in room.participants}")
            
            if not room:
                await manager.send_personal_message(
                    json.dumps({"error": "Room does not exist"}), websocket
                )
                continue
            if sender_id not in room.participants:
                await manager.send_personal_message(
                    json.dumps({"error": "You are not in this room"}), websocket
                )
                continue
            
            logger.info(f"Processing {room.room_type} message for room {room.id}")
            if room.room_type == "private":
                await handle_private_message(
                    user=user, room=room, message_content=message_content, ws=websocket
                )
            elif room.room_type == "group":
                await handle_group_message(
                    user=user, room=room, message_content=message_content, ws=websocket
                )
            else:
                logger.error(f"Unknown room type: {room.room_type}")
                await manager.send_personal_message(
                    json.dumps({"error": f"Unknown room type: {room.room_type}"}), websocket
                )

    except WebSocketDisconnect:
        try:
            rooms = await Room.find({"participants": sender_id}).to_list()
            for room in rooms:
                disconnect_message = {
                    "status": "offline",
                    "room_id": str(room.id),
                    "user_email": user.email,
                    "user_name": user.full_name,
                    "message": f"User {user.email} has disconnected",
                }

                for participant in room.participants:
                    if participant != sender_id:
                        await manager.broadcast_to_user(
                            json.dumps(disconnect_message), participant
                        )

            manager.disconnect(websocket)
            logger.info(f"User {user.email} disconnected from all rooms")

        except Exception as e:
            logger.error(f"Error handling disconnect for user {user.email}: {str(e)}")

    except Exception as e:
        await manager.send_personal_message(json.dumps({"error": str(e)}), websocket)
    finally:
        manager.disconnect(websocket)
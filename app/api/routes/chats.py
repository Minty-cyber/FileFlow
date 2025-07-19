import json
import logging
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.core.chat_config import manager
from typing import List
from app.api.deps import authenticate_ws
from app.models import User
from app.api.deps import SessionDep

from app.models import Room, Message
from bson import ObjectId

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def chat(websocket: WebSocket,session: SessionDep):
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
                logger.info(f"Logging the room_id being sent:{room_id} with type: {type(room_id)}")
                message_content = message_data.get("message")
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"error": "Invalid JSON Format"}),
                    websocket
                )
                continue
            room = await Room.find_one({"_id" : ObjectId(room_id)})
            logger.info(f"Room id : {room} with type: {type(room)} ")
            if not room:
                await manager.send_personal_message(
                    json.dumps({"error": "Room does not exist"}),
                    websocket
                )
                continue
            if sender_id not in room.participants:
                await manager.send_personal_message(
                    json.dumps({"error": "You are not in this room"}),
                    websocket
                )
                continue
            
            message = Message(
                room_id=room_id,
                sender_id=sender_id,
                message=message_content
            )
            await message.insert()
            
            
            for participant in room.participants:
                if participant != sender_id:
                    await manager.broadcast_to_user(
                        json.dumps({
                            "room_id": room_id,
                            "sender_id": sender_id,
                            "sender_email": sender_email,
                            "sender_name": sender_name,
                            "message": message_content,
                            "timestamp": message.timestamp.isoformat()
                        }),
                        participant
                    )
            await manager.send_personal_message(
                json.dumps({
                    "status": "sent",
                    "room_id": room_id,
                    "message": message_content,
                    "timestamp": message.timestamp.isoformat()
                }),
                websocket
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
                            json.dumps(disconnect_message),
                            participant
                        )
            
            manager.disconnect(websocket)
            logger.info(f"User {user.email} disconnected from all rooms")
            
        except Exception as e:
            logger.error(f"Error handling disconnect for user {user.email}: {str(e)}")
            
    except Exception as e:
        await manager.send_personal_message(
            json.dumps({"error": str(e)}),
            websocket
        )
    finally:
        manager.disconnect(websocket)
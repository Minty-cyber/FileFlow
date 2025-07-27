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
    
    try:
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
                    str(room.id)
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
    except Exception as e:
        logger.error(f"Error handling private message: {e}")
        await manager.send_personal_message(
            json.dumps({"error": "Failed to send message"}), ws
        )


async def handle_group_message(
    user: User, room: Room, message_content: str, ws: WebSocket
) -> Any:
    sender_id = str(user.id)
    sender_email = user.email
    sender_name = user.full_name

    try:
        message = Message(room_id=str(room.id), sender_id=sender_id, message=message_content)
        await message.insert()

        logger.info(f"Group message created for room {room.id}")
        
        broadcast_count = 0
        for participant in room.participants:
            if str(participant) != sender_id:
                logger.info(f"Broadcasting to participant: {participant}")
                
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
                    
                    await manager.broadcast_to_user(message_payload, str(participant), str(room.id))
                    broadcast_count += 1
                    logger.info(f"Successfully broadcast to {participant}")
                except Exception as e:
                    logger.error(f"Failed to broadcast to {participant}: {str(e)}")
        
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
    except Exception as e:
        logger.error(f"Error handling group message: {e}")
        await manager.send_personal_message(
            json.dumps({"error": "Failed to send message"}), ws
        )


@router.websocket("/ws/{room_id}")
async def chat(websocket: WebSocket, room_id: str, session: SessionDep):
    user = None
    
    try:
        user = await authenticate_ws(websocket, session, auto_accept=True)
        if not user:
            return  # WebSocket already closed
        
        sender_id = str(user.id)
        logger.info(f"Sender id: {sender_id}")
        
        try:
            room = await Room.find_one({"_id": ObjectId(room_id)})
            if not room:
                await websocket.close(code=4002, reason="Room does not exist")
                return
            if sender_id not in room.participants:
                await websocket.close(code=4003, reason="You are not in this room")
                return
        except Exception as e:
            logger.error(f"Error validating room {room_id}: {str(e)}")
            await websocket.close(code=4000, reason="Internal server error")
            return

        await manager.connect(websocket, user, room_id, already_accepted=True)

        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"WS received text: {data}")
                
                try:
                    message_data = json.loads(data)
                    message_content = message_data.get("message")
                    
                    if not message_content:
                        await manager.send_personal_message(
                            json.dumps({"error": "Message content is required"}), websocket
                        )
                        continue
                        
                except json.JSONDecodeError:
                    await manager.send_personal_message(
                        json.dumps({"error": "Invalid JSON Format"}), websocket
                    )
                    continue
                

                room = await Room.find_one({"_id": ObjectId(room_id)})
                if not room:
                    await manager.send_personal_message(
                        json.dumps({"error": "Room not found"}), websocket
                    )
                    continue
                
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
            logger.info(f"WebSocket disconnect detected for user {user.email if user else 'unknown'}")
        except Exception as e:
            logger.error(f"Error in websocket loop: {e}")
            try:
                await manager.send_personal_message(json.dumps({"error": str(e)}), websocket)
            except:
                pass 

    except Exception as e:
        logger.error(f"Error in websocket connection: {e}")
    finally:
        if user:
            try:
                sender_id = str(user.id)
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
                        if str(participant) != sender_id:
                            try:
                                await manager.broadcast_to_user(
                                    json.dumps(disconnect_message), str(participant), str(room.id)
                                )
                            except Exception as broadcast_error:
                                logger.error(f"Error broadcasting disconnect message: {broadcast_error}")

                logger.info(f"User {user.email} disconnected from all rooms")

            except Exception as e:
                logger.error(f"Error handling disconnect for user {user.email}: {str(e)}")
        
        manager.disconnect(websocket)
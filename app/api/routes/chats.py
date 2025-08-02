import json
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.models import User, Room, Message
from app.api.deps import authenticate_ws, SessionDep
from bson import ObjectId
from app.core.chat_config import manager
from datetime import datetime
from pymongo import DESCENDING


router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_private_message(
    user: User, room: Room, message_content: str, ws_id: str
) -> None:
    sender_id = str(user.id)
    sender_email = user.email
    sender_name = user.full_name

    try:
        message = Message(
            room_id=str(room.id), sender_id=sender_id, message=message_content
        )
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
                    str(room.id),
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
            ws_id,
        )
    except Exception as e:
        logger.error(f"Error handling private message: {e}")
        await manager.send_personal_message(
            json.dumps({"error": "Failed to send message"}), ws_id
        )


async def handle_group_message(
    user: User, room: Room, message_content: str, ws_id: str
) -> None:
    sender_id = str(user.id)
    sender_email = user.email
    sender_name = user.full_name
    try:
        message = Message(
            room_id=str(room.id), sender_id=sender_id, message=message_content
        )
        await message.insert()
        await manager.broadcast(
            json.dumps(
                {
                    "type": "group_message",
                    "room_id": str(room.id),
                    "room_name": room.room_name,
                    "sender_id": sender_id,
                    "sender_email": sender_email,
                    "sender_name": sender_name,
                    "message": message_content,
                    "timestamp": message.timestamp.isoformat(),
                }
            ),
            str(room.id),
            exclude_user_id=sender_id,
        )
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
            ws_id,
        )
    except Exception as e:
        logger.error(f"Error handling group message: {e}")
        await manager.send_personal_message(
            json.dumps({"error": "Failed to send message"}), ws_id
        )


async def send_missed_message(
    user: User,
    room: Room,
    ws_id: str,
    last_disconnected: str,
    session: SessionDep = Depends(),
):
    try:
        if not last_disconnected:
            logger.info("No last_disconnected timestamp provided")
            return

        last_disconnected_time = datetime.fromisoformat(last_disconnected)
        logger.info(
            f"[MISSED MSG] Processing missed messages for user {user.id} in room {room.id}"
        )
        logger.info(f"[MISSED MSG] Looking for messages after {last_disconnected_time}")

        query = {
            "room_id": str(room.id),
            "timestamp": {"$gt": last_disconnected_time},
        }
        logger.info(f"[MISSED MSG] Executing MongoDB query: {query}")

        messages = await Message.find(query).sort([("timestamp", 1)]).to_list()

        logger.info(f"[MISSED MSG] MongoDB returned {len(messages)} missed messages")

        if len(messages) == 0:
            logger.info("[MISSED MSG] No missed messages found")
            return

        for msg in messages:
            logger.info(
                f"[MISSED MSG] Message {i+1}: ID={msg.id}, "
                f"Room={msg.room_id}, Sender={msg.sender_id}, "
                f"Timestamp={msg.timestamp}, Content={msg.message[:50]}..."
            )

        # Send each missed message
        for message in messages:
            try:
                sender_id = message.sender_id
                sender = session.get(User, sender_id)
                logger.info(f"[USER_ID]: {sender}")

                message_data = {
                    "type": (
                        "group_message"
                        if room.room_type == "group"
                        else "private_message"
                    ),
                    "room_id": str(room.id),
                    "room_name": room.room_name,
                    "sender_id": sender_id,
                    "sender_email": sender.email if sender else "",
                    "sender_name": sender.full_name if sender else "",
                    "message": message.message,
                    "timestamp": message.timestamp.isoformat(),
                    "missed": True,
                }

                await manager.send_personal_message(json.dumps(message_data), ws_id)
                logger.info(f"[MISSED MSG] Sent missed message {i+1}/{len(messages)}")

                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(
                    f"[MISSED MSG] Error sending individual missed message: {e}"
                )

        logger.info(f"[MISSED MSG] Completed sending {len(messages)} missed messages")

    except Exception as e:
        logger.error(f"[MISSED MSG] Error in send_missed_message: {e}")


async def listen_pubsub(ws_id: str, room_id: str):
    try:
        pubsub = manager.redis.pubsub()
        await pubsub.subscribe(f"room:{room_id}")
        logger.info(f"[PUBSUB] Started listening for ws_id {ws_id} in room {room_id}")

        async for message in pubsub.listen():
            if message["type"] == "message":
                await manager.send_personal_message(message["data"], ws_id)
    except Exception as e:
        logger.error(f"[PUBSUB] PubSub listener error for ws_id {ws_id}: {e}")
    finally:
        await pubsub.unsubscribe(f"room:{room_id}")
        await pubsub.close()
        logger.info(f"[PUBSUB] Closed pubsub for ws_id {ws_id}")


@router.websocket("/ws/{room_id}")
async def chat(websocket: WebSocket, room_id: str, session: SessionDep):
    user = await authenticate_ws(websocket, session, auto_accept=True)
    if not user:
        return  # Connection will be closed by authenticate_ws

    sender_id = str(user.id)
    sender_email = user.email
    sender_name = user.full_name

    try:
        room = await Room.find_one({"_id": ObjectId(room_id)})
        if not room:
            await websocket.close(code=4002, reason="Room does not exist")
            return
        if sender_id not in room.participants:
            await websocket.close(code=4003, reason="You are not in this room")
            return
    except Exception as e:
        logger.error(f"Error validating room {room_id}: {e}")
        await websocket.close(code=4000, reason="Internal server error")
        return
    ws_id, last_disconnected = await manager.connect(
        websocket, user, room_id, already_accepted=True
    )

    logger.info(
        f"[CONNECTION] User {sender_email} connected with ws_id={ws_id}, "
        f"last_disconnected={last_disconnected}"
    )

    if last_disconnected:
        logger.info(f"[CONNECTION] Sending missed messages to user {sender_id}")
        await send_missed_message(user, room, ws_id, last_disconnected, session)

        await manager.cleanup_disconnect_timestamp(sender_id, room_id)
        logger.info(
            f"[CONNECTION] Cleaned up disconnect timestamp for user {sender_id}"
        )
    else:
        logger.info(f"[CONNECTION] No missed messages to send for user {sender_id}")

    pubsub_task = asyncio.create_task(listen_pubsub(ws_id, room_id))
    logger.info(f"[CONNECTION] Started pubsub task for user {sender_id}")

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"[WS] Received message from {sender_email}: {data}")

            try:
                message_data = json.loads(data)
                message_content = message_data.get("message")
                if not message_content:
                    await manager.send_personal_message(
                        json.dumps({"error": "Message content is required"}), ws_id
                    )
                    continue
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"error": "Invalid JSON Format"}), ws_id
                )
                continue

            if room.room_type == "private":
                await handle_private_message(
                    user=user, room=room, message_content=message_content, ws_id=ws_id
                )
            elif room.room_type == "group":
                await handle_group_message(
                    user=user, room=room, message_content=message_content, ws_id=ws_id
                )

    except WebSocketDisconnect:
        logger.info(f"[DISCONNECT] User {user.email} disconnected from room {room_id}")
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error for user {user.email}: {e}")
        await manager.send_personal_message(json.dumps({"error": str(e)}), ws_id)
    finally:
        pubsub_task.cancel()
        await manager.disconnect(ws_id)
        logger.info(f"[CLEANUP] Cleaned up connection for user {user.email}")

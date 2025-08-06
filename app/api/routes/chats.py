from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.models import User, Room, Message
from app.api.deps import authenticate_ws, SessionDep
from bson import ObjectId
import json
import logging
from app.core.chat_config import manager
import asyncio
from datetime import datetime, timedelta
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
        logger.info(
            f"Stored message in MongoDB: room_id={str(room.id)}, sender_id={sender_id}, message={message_content}"
        )
        message_data = json.dumps(
            {
                "room_id": str(room.id),
                "sender_id": sender_id,
                "sender_email": sender_email,
                "sender_name": sender_name,
                "message": message_content,
                "timestamp": message.timestamp.isoformat(),
            }
        )
        await manager.redis.zadd(
            f"room:{str(room.id)}:messages",
            {message_data: message.timestamp.timestamp()},
        )
        await manager.cache_message(str(room.id))
        logger.info(f"Cached message in Redis for room {str(room.id)}")
        for participant in room.participants:
            if participant != sender_id:
                await manager.broadcast_to_user(message_data, participant, str(room.id))
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
        logger.info(
            f"Stored group message in MongoDB: room_id={str(room.id)}, sender_id={sender_id}, message={message_content}"
        )
        message_data = json.dumps(
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
        )
        await manager.redis.zadd(
            f"room:{str(room.id)}:messages",
            {message_data: message.timestamp.timestamp()},
        )
        await manager.cache_message(str(room.id))
        logger.info(f"Cached group message in Redis for room {str(room.id)}")
        await manager.broadcast(message_data, str(room.id), exclude_user_id=sender_id)
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


async def listen_pubsub(ws_id: str, room_id: str):
    try:
        pubsub = manager.redis.pubsub()
        await pubsub.subscribe(f"room:{room_id}")
        logger.info(f"[PUBSUB] Started listening for ws_id {ws_id} in room {room_id}")
        async for message in pubsub.listen():
            if message["type"] == "message":
                await manager.send_personal_message(message["data"], ws_id)
                logger.info(
                    f"[PUBSUB] Sent PubSub message to ws_id {ws_id}: {message['data']}"
                )
    except Exception as e:
        logger.error(f"[PUBSUB] PubSub listener error for ws_id {ws_id}: {e}")
    finally:
        await pubsub.unsubscribe(f"room:{room_id}")
        await pubsub.close()
        logger.info(f"[PUBSUB] Closed pubsub for ws_id {ws_id}")


async def send_missed_messages(
    user: User, room: Room, ws_id: str, last_disconnect: str
):
    try:
        if not last_disconnect:
            logger.info(
                f"[MISSED MSG] No last_disconnect timestamp for user {user.email} in room {room.id}"
            )
            await manager.send_personal_message(
                json.dumps({"status": "info", "message": "No missed messages"}), ws_id
            )
            return

        last_disconnect_time = datetime.fromisoformat(last_disconnect)
        logger.info(
            f"[MISSED MSG] Fetching missed messages for user {user.email} in room {room.id} since {last_disconnect_time.isoformat()}"
        )

        messages = []
        cache_key = f"room:{str(room.id)}:messages"
        logger.info(
            f"[MISSED MSG] Checking Redis cache:\n"
            f"- Key: {cache_key}\n"
            f"- From timestamp: {last_disconnect_time.timestamp()}\n"
            f"- Human readable time: {last_disconnect_time.isoformat()}"
        )

        cached_messages = await manager.redis.zrangebyscore(
            cache_key,
            min=last_disconnect_time.timestamp(),
            max="+inf",
            withscores=True,  # Get timestamps for verification
        )

        logger.info(
            f"[MISSED MSG] Found {len(cached_messages)} cached messages in Redis for room {room.id}"
        )
        for msg, score in cached_messages:
            try:
                msg_data = json.loads(msg)
                msg_time = datetime.fromtimestamp(score)
                logger.info(
                    f"[MISSED MSG] Processing cached message:\n"
                    f"- Score (timestamp): {score}\n"
                    f"- Message time: {msg_time.isoformat()}\n"
                    f"- Message: {msg_data.get('message', '')[:50]}..."
                )
                msg_data["missed"] = True
                messages.append(msg_data)
            except json.JSONDecodeError as e:
                logger.error(f"[MISSED MSG] Failed to parse cached message: {e}")

        if not messages:
            logger.info(
                f"[MISSED MSG] No cached messages found, querying MongoDB for room {room.id}"
            )
            mongo_messages = (
                await Message.find(
                    {
                        "room_id": str(room.id),
                        "timestamp": {"$gt": last_disconnect_time},
                    }
                )
                .sort([("timestamp", DESCENDING)])
                .to_list()
            )
            logger.info(
                f"[MISSED MSG] Found {len(mongo_messages)} messages in MongoDB for user {user.email}"
            )
            for msg in mongo_messages:
                sender = await User.find_one({"_id": ObjectId(msg.sender_id)})
                messages.append(
                    {
                        "type": (
                            "group_message"
                            if room.room_type == "group"
                            else "private_message"
                        ),
                        "room_id": str(room.id),
                        "room_name": room.room_name,
                        "sender_id": msg.sender_id,
                        "sender_email": sender.email if sender else "",
                        "sender_name": sender.full_name if sender else "",
                        "message": msg.message,
                        "timestamp": msg.timestamp.isoformat(),
                        "missed": True,
                    }
                )

        for msg in messages:
            await manager.send_personal_message(json.dumps(msg), ws_id)

            await asyncio.sleep(0.01)  #

        if not messages:
            logger.info(f"[MISSED MSG] No missed messages found for user {user.email}")
            await manager.send_personal_message(
                json.dumps({"status": "info", "message": "No missed messages"}), ws_id
            )
    except Exception as e:
        logger.error(
            f"[MISSED MSG] Error sending missed messages to user {user.email}: {e}"
        )
        await manager.send_personal_message(
            json.dumps({"error": "Failed to load missed messages"}), ws_id
        )


@router.websocket("/ws/{room_id}")
async def chat(websocket: WebSocket, room_id: str, session: SessionDep):
    user = await authenticate_ws(websocket, session, auto_accept=True)
    if not user:
        return

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
        logger.error(f"[CONNECTION] Error validating room {room_id}: {e}")
        await websocket.close(code=4000, reason="Internal server error")
        return

    ws_id = await manager.connect(websocket, user, room_id, already_accepted=True)
    
    last_seen_key = f"user:{sender_id}:room:{room_id}:last_seen"
    last_seen = await manager.redis.get(last_seen_key)
    
    logger.info(
        f"[CONNECTION] User {sender_email} connected:\n"
        f"- ws_id: {ws_id}\n"
        f"- last_seen_key: {last_seen_key}\n"
        f"- last_seen: {last_seen or 'None'}"
    )

    if last_seen:
        logger.info(f"[CONNECTION] Sending missed messages to user {sender_id}")
        await send_missed_messages(user, room, ws_id, last_seen)

    pubsub_task = asyncio.create_task(listen_pubsub(ws_id, room_id))
    logger.info(f"[CONNECTION] Started pubsub task for user {sender_id}")

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"[WS] Received message from {sender_email}: {data}")
            
            current_time = datetime.utcnow().isoformat()
            await manager.redis.set(last_seen_key, current_time)
            
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
        
        current_time = datetime.utcnow().isoformat()
        await manager.redis.set(last_seen_key, current_time)
        
        await manager.disconnect(ws_id, user=user)
        logger.info(f"[CLEANUP] Cleaned up connection for user {user.email}")


async def send_missed_messages(
    user: User, room: Room, ws_id: str, last_seen: str
):
    try:
        if not last_seen:
            logger.info(
                f"[MISSED MSG] No last_seen timestamp for user {user.email} in room {room.id}"
            )
            await manager.send_personal_message(
                json.dumps({"status": "info", "message": "No missed messages"}), ws_id
            )
            return

        last_seen_time = datetime.fromisoformat(last_seen)
        logger.info(
            f"[MISSED MSG] Fetching missed messages for user {user.email} in room {room.id} since {last_seen_time.isoformat()}"
        )

        messages = []
        cache_key = f"room:{str(room.id)}:messages"
        logger.info(
            f"[MISSED MSG] Checking Redis cache:\n"
            f"- Key: {cache_key}\n"
            f"- From timestamp: {last_seen_time.timestamp()}\n"
            f"- Human readable time: {last_seen_time.isoformat()}"
        )

        cached_messages = await manager.redis.zrangebyscore(
            cache_key,
            min=f"({last_seen_time.timestamp()}",  # Exclude exact timestamp
            max="+inf",
            withscores=True,
        )

        logger.info(
            f"[MISSED MSG] Found {len(cached_messages)} cached messages in Redis for room {room.id}"
        )
        
        for msg, score in cached_messages:
            try:
                msg_data = json.loads(msg)
                msg_time = datetime.fromtimestamp(score)
                logger.info(
                    f"[MISSED MSG] Processing cached message:\n"
                    f"- Score (timestamp): {score}\n"
                    f"- Message time: {msg_time.isoformat()}\n"
                    f"- Message: {msg_data.get('message', '')[:50]}..."
                )
                msg_data["missed"] = True
                messages.append(msg_data)
            except json.JSONDecodeError as e:
                logger.error(f"[MISSED MSG] Failed to parse cached message: {e}")

        if not messages:
            logger.info(
                f"[MISSED MSG] No cached messages found, querying MongoDB for room {room.id}"
            )
            mongo_messages = (
                await Message.find(
                    {
                        "room_id": str(room.id),
                        "timestamp": {"$gt": last_seen_time},
                    }
                )
                .sort([("timestamp", DESCENDING)])
                .to_list()
            )
            logger.info(
                f"[MISSED MSG] Found {len(mongo_messages)} messages in MongoDB for user {user.email}"
            )
            for msg in mongo_messages:
                sender = await User.find_one({"_id": ObjectId(msg.sender_id)})
                messages.append(
                    {
                        "type": (
                            "group_message"
                            if room.room_type == "group"
                            else "private_message"
                        ),
                        "room_id": str(room.id),
                        "room_name": room.room_name,
                        "sender_id": msg.sender_id,
                        "sender_email": sender.email if sender else "",
                        "sender_name": sender.full_name if sender else "",
                        "message": msg.message,
                        "timestamp": msg.timestamp.isoformat(),
                        "missed": True,
                    }
                )

        messages.sort(key=lambda x: x['timestamp'])

        for msg in messages:
            await manager.send_personal_message(json.dumps(msg), ws_id)
            await asyncio.sleep(0.01)

        if not messages:
            logger.info(f"[MISSED MSG] No missed messages found for user {user.email}")
            await manager.send_personal_message(
                json.dumps({"status": "info", "message": "No missed messages"}), ws_id
            )
    except Exception as e:
        logger.error(
            f"[MISSED MSG] Error sending missed messages to user {user.email}: {e}"
        )
        await manager.send_personal_message(
            json.dumps({"error": "Failed to load missed messages"}), ws_id
        )

async def disconnect(self, ws_id: str, user=None):
    try:
        ws_data = await self.redis.hgetall(f"ws:{ws_id}")
        if not ws_data:
            logger.warning(f"No WebSocket data found for ws_id: {ws_id}")
            return

        user_id = ws_data.get("user_id")
        room_id = ws_data.get("room_id")

        if user_id and room_id:
            if await self.redis.sismember(f"room:{room_id}:users", user_id):
                logger.info(
                    f"Removing user {user.email if user else user_id} from room {room_id}"
                )
                removed = await self.redis.srem(f"room:{room_id}:users", user_id)
                logger.info(
                    f"User removal result: {removed} (1=success, 0=not found)"
                )

            disconnect_message = json.dumps(
                {
                    "status": "offline",
                    "room_id": room_id,
                    "user_id": user_id,
                    "user_email": user.email if user else "",
                    "user_name": user.full_name if user else "",
                    "message": f"User {user.email if user else user_id} has disconnected",
                }
            )
            await self.redis.publish(f"room:{room_id}", disconnect_message)

            remaining_users = await self.redis.smembers(f"room:{room_id}:users")
            logger.info(
                f"User {user_id} disconnected from room {room_id}. "
                f"Remaining users in room: {remaining_users}"
            )

        await self.redis.delete(f"ws:{ws_id}")
        if ws_id in self.local_websockets:
            del self.local_websockets[ws_id]
    except Exception as e:
        logger.error(f"Error during disconnect: {e}")
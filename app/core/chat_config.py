import logging
import uuid
import json
import redis.asyncio as redis

from fastapi import WebSocket
from typing import Optional, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(
        self, redis_host: str = "redis", redis_port: int = 6379, redis_db: int = 0
    ):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, db=redis_db, decode_responses=True
        )
        self.pubsub = self.redis.pubsub()
        self.local_websockets: Dict[str, WebSocket] = {}

    async def connect(
        self, websocket: WebSocket, user, room_id: str, already_accepted: bool = False
    ) -> Tuple[str, Optional[str]]: 
        ws_id = None
        try:
            ws_id = str(uuid.uuid4())
            if not already_accepted:
                await websocket.accept()

            user_id = str(user.id)
            await self.redis.hset(
                f"ws:{ws_id}", mapping={"user_id": user_id, "room_id": room_id}
            )
            await self.redis.sadd(f"room:{room_id}:users", user_id)
            self.local_websockets[ws_id] = websocket
            
            last_disconnected = await self.redis.get(
                f"user:{user_id}:room:{room_id}:last_disconnected"
            )

            logger.info(
                f"User {user.email} connected to room {room_id}. "
                f"Last disconnected: {last_disconnected}. "
                f"Total users in room: {await self.get_user_connection_count(room_id)}"
            )
            return ws_id, last_disconnected
        except Exception as e:
            logger.error(f"Error connecting websocket: {e}")
            if ws_id and ws_id in self.local_websockets:
                del self.local_websockets[ws_id]
            if not already_accepted:
                await websocket.close(code=4000, reason="Connection failed")
            raise

    async def cleanup_disconnect_timestamp(self, user_id: str, room_id: str):
        try:
            await self.redis.delete(f"user:{user_id}:room:{room_id}:last_disconnected")
            logger.info(f"Cleaned up disconnect timestamp for user {user_id} in room {room_id}")
        except Exception as e:
            logger.error(f"Error cleaning up disconnect timestamp: {e}")

    async def disconnect(self, ws_id: str):
        try:
            ws_data = await self.redis.hgetall(f"ws:{ws_id}")
            if not ws_data:
                logger.warning(f"No WebSocket data found for ws_id: {ws_id}")
                return

            user_id = ws_data.get("user_id")
            room_id = ws_data.get("room_id")

            if user_id and room_id:
                await self.redis.srem(f"room:{room_id}:users", user_id)
                
                disconnect_time = datetime.utcnow().isoformat()
                await self.redis.set(
                    f"user:{user_id}:room:{room_id}:last_disconnected",
                    disconnect_time,
                )
                
                disconnect_message = json.dumps(
                    {
                        "status": "offline",
                        "room_id": room_id,
                        "user_id": user_id,
                        "user_email": "",
                        "user_name": "",
                        "message": f"User {user_id} has disconnected",
                    }
                )
                await self.redis.publish(f"room:{room_id}", disconnect_message)
                logger.info(
                    f"User {user_id} disconnected from room {room_id}. "
                    f"Stored disconnect timestamp: {disconnect_time}"
                )

            await self.redis.delete(f"ws:{ws_id}")
            if ws_id in self.local_websockets:
                del self.local_websockets[ws_id]
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def send_personal_message(self, message: str, ws_id: str):
        try:
            websocket = self.local_websockets.get(ws_id)
            if websocket:
                await websocket.send_text(message)
            else:
                logger.warning(f"No WebSocket found for ws_id: {ws_id}")
        except Exception as e:
            logger.error(f"Failed to send personal message to ws_id {ws_id}: {e}")
            await self.disconnect(ws_id)

    async def broadcast_to_user(self, message: str, user_id: str, room_id: str):
        try:
            if await self.redis.sismember(f"room:{room_id}:users", user_id):
                await self.redis.publish(f"room:{room_id}", message)
                logger.info(f"Broadcasted to user {user_id} in room {room_id}")
        except Exception as e:
            logger.error(
                f"Failed to broadcast to user {user_id} in room {room_id}: {e}"
            )

    async def broadcast(self, message: str, room_id: str, exclude_user_id: str = None):
        try:
            if exclude_user_id:
                users = await self.redis.smembers(f"room:{room_id}:users")
                if len(users) > 1 or (len(users) == 1 and exclude_user_id not in users):
                    await self.redis.publish(f"room:{room_id}", message)
            else:
                await self.redis.publish(f"room:{room_id}", message)
            logger.info(f"Broadcasted message to room {room_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast to room {room_id}: {e}")

    async def get_room_id(self, ws_id: str) -> Optional[str]:
        try:
            ws_data = await self.redis.hgetall(f"ws:{ws_id}")
            return ws_data.get("room_id")
        except Exception as e:
            logger.error(f"Error getting room_id for ws_id {ws_id}: {e}")
            return None

    async def get_connected_users(self, room_id: str = None) -> List[str]:
        try:
            if room_id:
                return list(await self.redis.smembers(f"room:{room_id}:users"))
            all_users = set()
            async for key in self.redis.scan_iter("room:*:users"):
                users = await self.redis.smembers(key)
                all_users.update(users)
            return list(all_users)
        except Exception as e:
            logger.error(f"Error getting connected users: {e}")
            return []

    async def get_user_connection_count(self, room_id: str = None) -> int:
        try:
            if room_id:
                return await self.redis.scard(f"room:{room_id}:users")
            return len(await self.get_connected_users())
        except Exception as e:
            logger.error(f"Error getting user connection count: {e}")
            return 0


manager = ConnectionManager()
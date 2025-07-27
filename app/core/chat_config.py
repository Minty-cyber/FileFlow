import logging
from fastapi import WebSocket
from typing import Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.user_connections: Dict[str, Dict[str, List[WebSocket]]] = {}
        self.connection_room_map: Dict[WebSocket, tuple[str, str]] = {}
        self.connection_states: Dict[WebSocket, str] = {} 

    async def connect(self, websocket: WebSocket, user, room_id: str, already_accepted: bool = False):
        try:
            
            if not already_accepted and websocket not in self.connection_states:
                await websocket.accept()
                self.connection_states[websocket] = "connected"
            elif already_accepted:
                self.connection_states[websocket] = "connected"
            
            user_id = str(user.id)
            if user_id not in self.user_connections:
                self.user_connections[user_id] = {}
            if room_id not in self.user_connections[user_id]:
                self.user_connections[user_id][room_id] = []
            
            if websocket not in self.user_connections[user_id][room_id]:
                self.user_connections[user_id][room_id].append(websocket)
            
            self.connection_room_map[websocket] = (user_id, room_id)
            logger.info(f"User {user.email} connected to room {room_id}. Total connections: {len(self.user_connections[user_id][room_id])}")
        except Exception as e:
            logger.error(f"Error connecting websocket: {e}")
            self.disconnect(websocket)
            raise

    def disconnect(self, websocket: WebSocket):
        try:
            if websocket in self.connection_room_map:
                user_id, room_id = self.connection_room_map[websocket]
                if user_id in self.user_connections and room_id in self.user_connections[user_id]:
                    if websocket in self.user_connections[user_id][room_id]:
                        self.user_connections[user_id][room_id].remove(websocket)
                        logger.info(f"User {user_id} disconnected from room {room_id}")
                    if not self.user_connections[user_id][room_id]:
                        del self.user_connections[user_id][room_id]
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                del self.connection_room_map[websocket]
                logger.info(f"User {user_id} disconnected")
            
            if websocket in self.connection_states:
                del self.connection_states[websocket]
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            if websocket in self.connection_states and self.connection_states[websocket] == "connected":
                await websocket.send_text(message)
            else:
                logger.warning("Attempted to send message to disconnected websocket")
                self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_user(self, message: str, user_id: str, room_id: str = None):
        if user_id in self.user_connections:
            if room_id and room_id in self.user_connections[user_id]:
                connections = self.user_connections[user_id][room_id].copy()
            else:
                connections = []
                for room_connections in self.user_connections[user_id].values():
                    connections.extend(room_connections)
            
            for connection in connections:
                try:
                    if connection in self.connection_states and self.connection_states[connection] == "connected":
                        await connection.send_text(message)
                    else:
                        self.disconnect(connection)
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_id} in room {room_id}: {str(e)}")
                    self.disconnect(connection)

    async def broadcast(self, message: str, room_id: str, exclude_user_id: str = None):
        for user_id in self.user_connections:
            if user_id == exclude_user_id:
                continue
            if room_id in self.user_connections[user_id]:
                connections = self.user_connections[user_id][room_id].copy()
                for connection in connections:
                    try:
                        if connection in self.connection_states and self.connection_states[connection] == "connected":
                            await connection.send_text(message)
                        else:
                            self.disconnect(connection)
                    except Exception as e:
                        logger.error(f"Failed to broadcast to user {user_id} in room {room_id}: {str(e)}")
                        self.disconnect(connection)

    def get_room_id(self, websocket: WebSocket) -> Optional[str]:
        if websocket in self.connection_room_map:
            return self.connection_room_map[websocket][1]
        return None

    def get_connected_users(self, room_id: str = None) -> List[str]:
        if room_id:
            return [user_id for user_id in self.user_connections if room_id in self.user_connections[user_id]]
        return list(self.user_connections.keys())

    def get_user_connection_count(self, user_id: str, room_id: str = None) -> int:
        if user_id in self.user_connections:
            if room_id:
                return len(self.user_connections[user_id].get(room_id, []))
            return sum(len(connections) for connections in self.user_connections[user_id].values())
        return 0

manager = ConnectionManager()
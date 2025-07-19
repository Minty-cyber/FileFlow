import logging
from fastapi import WebSocket
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.user_connections: Dict[str, List[WebSocket]] = {}
        self.connection_user_map: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user):
        user_id = str(user.id)
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        
        self.user_connections[user_id].append(websocket)
        self.connection_user_map[websocket] = user_id
        
        logger.info(f"User {user.email} connected. Total connections for user: {len(self.user_connections[user_id])}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connection_user_map:
            user_id = self.connection_user_map[websocket]
            if user_id in self.user_connections:
                if websocket in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(websocket)

                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
        
            del self.connection_user_map[websocket]
            
            logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_user(self, message: str, user_id: str):
        if user_id in self.user_connections:
            connections = self.user_connections[user_id].copy()
            
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_id}: {str(e)}")
                    self.disconnect(connection)

    async def broadcast(self, message: str):
        for user_id, connections in list(self.user_connections.items()):
            connections_copy = connections.copy()
            
            for connection in connections_copy:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_id}: {str(e)}")
                    self.disconnect(connection)

    def get_connected_users(self) -> List[str]:
        return list(self.user_connections.keys())

    def get_user_connection_count(self, user_id: str) -> int:
        return len(self.user_connections.get(user_id, []))

manager = ConnectionManager()
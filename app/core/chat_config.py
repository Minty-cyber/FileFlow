from fastapi import WebSocket
from typing import List, Dict
import logfire
from app.models import User

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {} 

    async def connect(self, websocket: WebSocket, user: User):
        self.active_connections.append(websocket)
        user_id = str(user.id) 
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)
        logfire.info(f"WebSocket connected for user {user.id}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        for user_id, connections in list(self.user_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.user_connections[user_id]
                logfire.info(f"WebSocket disconnected for user {user_id}")
                break

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logfire.error(f"Failed to send personal message: {str(e)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logfire.error(f"Failed to broadcast message to a connection: {str(e)}")

    async def broadcast_to_user(self, message: str, user_id: str):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logfire.error(f"Failed to broadcast to user {user_id}: {str(e)}")

manager = ConnectionManager()
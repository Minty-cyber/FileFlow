from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.core.chat_config import manager
from typing import List
from app.api.deps import authenticate_ws
from app.models import User
from app.api.deps import SessionDep

router = APIRouter()

@router.websocket("/test")
async def chat_endpoint(websocket: WebSocket, session: SessionDep):
    await websocket.accept()  # Accept the WebSocket connection
    user = await authenticate_ws(websocket, session)
    if not user:
        return  # WebSocket already closed by authenticate_ws

    await manager.connect(websocket, user)  # Connect after authentication
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message from {user.email}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"User {user.email} has disconnected")
    except Exception as e:
        manager.disconnect(websocket)
        await manager.broadcast(f"An error occurred: {str(e)}")
    finally:
        manager.disconnect(websocket)
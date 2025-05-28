from fastapi import APIRouter
from app.api.routes import users, groups, chats, logs 

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
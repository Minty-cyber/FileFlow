from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from app.utils import log_exception_to_db
from contextlib import asynccontextmanager
from fastapi.routing import APIRoute
from app.core.config import settings
from app.api.main import api_router
from app.api.deps import get_current_user, use_oauth2, engine

from app.initializer import run_initializer
from app.core.config import init_mongodb
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_route_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
       
        logger.info("Running PostgreSQL database initializer")
        run_initializer()
        logger.info("PostgreSQL database initializer completed")

        
        logger.info("Initializing MongoDB connection")
        await init_mongodb()
        logger.info("MongoDB initialization completed")

        yield 
       
       
        
    except Exception as e:
        logger.error(f"Error during application lifecycle: {e}")
        raise


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=generate_route_id,
)

# settings.setup_logfire(app)


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def db_exception_handler(request: Request, exc: Exception):
    username = None
    try:
        token = await use_oauth2(request)
        if token:
            with Session(engine) as session:
                user = await get_current_user(session, token)
                username = user.full_name
    except Exception as e:
        print(f"Error resolving current_user: {e}")

    with Session(engine) as session:
        log_exception_to_db(session, exc, request, username)

    return JSONResponse(
        status_code=500, content={"detail": "An internal server error occurred."}
    )

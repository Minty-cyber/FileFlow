from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.routing import APIRoute
from app.core.config import settings
from app.api.main import api_router
from app.initializer import run_initializer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_route_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Running database initializer")
    run_initializer() 
    logger.info("Database initializer completed")
    yield
    



app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=generate_route_id
    
)

settings.setup_logfire(app)


@app.on_event("startup") # This will run when the server starts
def startup_event():
    logger.info("Running database initializer")
    run_initializer() 
    logger.info("Database initializer completed")

app.include_router(api_router, prefix=settings.API_V1_STR)


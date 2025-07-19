import secrets
import logging
import os
from typing import Annotated, Any, Literal, Optional
from app.models import Post, Room, Message

import logfire
from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import (
    AnyUrl,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    MongoDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo import MongoClient
from pymongo.database import Database
from typing_extensions import Self

logger = logging.getLogger(__name__)

DOCUMENT_MODELS = [Post, Room, Message]


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRATION: int = 60 * 24 * 7
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    PROJECT_NAME: str

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    MONGODB_SERVER: str
    MONGODB_PORT: int = 27017
    MONGODB_USER: str
    MONGODB_PASSWORD: str
    MONGODB_DB: str

    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    EMAIL_TEST_USER: EmailStr
    EMAIL_TEST_USER_PASSWORD: str
    TEST_USER: str

    # Monitoring Configuration
    # LOGFIRE_TOKEN: str
    # LOGFIRE_SERVICE_NAME: str

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @computed_field
    @property
    def MONGODB_URI(self) -> str:
        return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_SERVER}:{self.MONGODB_PORT}/{self.MONGODB_DB}?authSource=admin"


class MongoDBManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database_name: Optional[str] = None

    async def connect(self, mongodb_uri: str, database_name: str) -> None:
        try:
            logger.info("Attempting to connect to MongoDB...")
            self.client = AsyncIOMotorClient(
                mongodb_uri, serverSelectionTimeoutMS=5000 
            )
            self.database_name = database_name

            await self.client.admin.command("ping")
            logger.info("MongoDB ping successful")
            await init_beanie(
                database=self.client[database_name], 
                document_models=DOCUMENT_MODELS
            )

            logger.info(f"Successfully connected to MongoDB database: {database_name}")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            if self.client:
                self.client.close()
            self.client = None
            self.database_name = None
            raise

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
            self.client = None
            self.database_name = None

    def get_database(self) -> Database:
        if not self.client or not self.database_name:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")

        return self.client[self.database_name]

    def get_sync_client(self, mongodb_uri: MongoDsn) -> MongoClient:
        return MongoClient(str(mongodb_uri))

    @property
    def is_connected(self) -> bool:
        return self.client is not None


settings = Settings()
mongodb_manager = MongoDBManager()


async def init_mongodb() -> None:
    logger.info("Initializing MongoDB connection...")
    database_name = settings.MONGODB_DB

    try:
        if mongodb_manager.is_connected:
            logger.info("MongoDB already connected")
            return

        await mongodb_manager.connect(
            mongodb_uri=settings.MONGODB_URI, database_name=database_name
        )
        logger.info("MongoDB initialization completed successfully")
    except Exception as e:
        logger.error(f"MongoDB initialization failed: {str(e)}")
        raise 

#
# def get_mongodb_client() -> MongoClient:
#
#     return mongodb_manager.get_sync_client(settings.MONGODB_URI)
# def
#     return mongodb_manager.get_database()

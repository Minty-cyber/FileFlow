import secrets
import logfire
from pydantic_core import MultiHostUrl
from pydantic import(
    AnyUrl,
    EmailStr,
    BeforeValidator,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator
)
from typing_extensions import Self
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated, Any, Literal
from fastapi import FastAPI

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = '.env',
        env_ignore_empty=True,
        extra="ignore",
        
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRATION: int = 60
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    PROJECT_NAME: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB : str 
    
    
    MAILJET_API_KEY: str
    MAILJET_SECRET_KEY: str
    
    LOGFIRE_TOKEN: str
    LOGFIRE_SERVICE_NAME: str
    # LOGFIRE_CONSOLE_LOG: bool = True
    # LOGFIRE_SAMPLE_RATE: float
    
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB
        )
        
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    EMAIL_TEST_USER: EmailStr
    EMAIL_TEST_USER_PASSWORD: str
    TEST_USER: str
    SECRET_KEY: str
    
    

    def setup_logfire(self, app:FastAPI) -> None:
        logfire.configure(
            token=self.LOGFIRE_TOKEN,
            service_name=self.LOGFIRE_SERVICE_NAME,
            
        )
        logfire.instrument_fastapi(app)
        logfire.instrument_pydantic()
    
    
settings = Settings()



import secrets
from pydantic_core import MultiHostUrl
from pydantic import(
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator
)
from typing_extensions import Self
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated, Any, Literal

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
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DATABASE_NAME : str = ""
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DATABASE_NAME
        )
        
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    
    
    
settings = Settings()

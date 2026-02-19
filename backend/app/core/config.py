from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator, ValidationInfo
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NexusAI"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Postgres
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "job_aggregator"
    SQLALCHEMY_DATABASE_URI: Optional[Union[PostgresDsn, str]] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        
        # We need to construct the URL manually if it's not provided
        # The values must be accessed from the info.data dictionary in Pydantic v2
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )

    # Mongo
    MONGO_URI: str = "mongodb://mongo:27017/job_aggregator"
    MONGO_DB_NAME: str = "job_aggregator"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

from pydantic_settings import BaseSettings
from typing import Optional
import os

# Disable .env file loading to avoid errors
os.environ.setdefault("DEMO_MODE", "true")


class Settings(BaseSettings):
    # App
    APP_NAME: str = "EventDiscovery AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Demo Mode (when no database available)
    DEMO_MODE: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/eventdiscovery"
    DATABASE_ASYNC_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eventdiscovery"
    
    # AI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = None
        case_sensitive = True


settings = Settings()

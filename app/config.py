import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "StartupOps AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Security & Tokens
    APP_SECRET_KEY: str = "super_secret_jwt_and_session_signing_key_32bytes_minimum!"
    ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Gemini & AI
    GOOGLE_AI_STUDIO_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Database & Redis
    DATABASE_URL: str = "sqlite+aiosqlite:///./startupops.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Frontend / Backend URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # Integrations OAuth Credentials
    GITHUB_CLIENT_ID: Optional[str] = "gh_test_client_id"
    GITHUB_CLIENT_SECRET: Optional[str] = "gh_test_client_secret"
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/github/callback"

    GOOGLE_CLIENT_ID: Optional[str] = "google_test_client_id"
    GOOGLE_CLIENT_SECRET: Optional[str] = "google_test_client_secret"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/gmail/callback"

    SLACK_CLIENT_ID: Optional[str] = "slack_test_client_id"
    SLACK_CLIENT_SECRET: Optional[str] = "slack_test_client_secret"
    SLACK_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/slack/callback"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

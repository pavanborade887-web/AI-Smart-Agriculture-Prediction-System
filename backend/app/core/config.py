from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[3] / ".env", env_file_encoding="utf-8", extra="ignore")
    environment: str = "development"
    database_url: str = "sqlite:///./agri.db"
    jwt_secret_key: str = "development-only-secret-change-before-deploying"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    frontend_origin: str = "http://localhost:5173"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    uploads_dir: str = "uploads"
    model_dir: str = "models"
    max_upload_size_mb: int = 10
    openweather_api_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret(cls, value: str) -> str:
        if value == "development-only-secret-change-before-deploying":
            return value
        if len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must have at least 32 characters")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

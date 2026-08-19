from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    app_name: str = "Ayman Naeem Portfolio API"
    database_url: str = "sqlite+aiosqlite:///./portfolio.db"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    api_public_url: str = "http://localhost:8000"
    local_media_dir: str = "uploads"
    jwt_secret_key: str = Field("development-only-change-me-32-chars", min_length=24)
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    max_image_upload_mb: int = 15
    max_video_upload_mb: int = 200
    max_request_attachment_mb: int = 10
    resend_api_key: str = ""
    email_from: str = "portfolio@example.com"
    email_to: str = ""
    turnstile_secret_key: str = ""
    github_username: str = ""
    github_token: str = ""
    log_level: str = "INFO"

    @property
    def cors_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

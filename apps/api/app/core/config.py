from functools import lru_cache
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEVELOPMENT_JWT_SECRET = "development-only-change-me-32-chars"


def _normalize_database_url(value: str) -> str:
    """Convert provider-style PostgreSQL URLs into SQLAlchemy asyncpg URLs."""
    if value.startswith("postgres://"):
        value = "postgresql://" + value.removeprefix("postgres://")
    if value.startswith("postgresql://"):
        value = "postgresql+asyncpg://" + value.removeprefix("postgresql://")

    parsed = urlsplit(value)
    if parsed.scheme == "postgresql+asyncpg":
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        # asyncpg accepts `ssl`; provider URLs commonly expose `sslmode`.
        if "sslmode" in query and "ssl" not in query:
            query["ssl"] = query.pop("sslmode")
        value = urlunsplit(parsed._replace(query=urlencode(query)))
    return value


def _normalize_origin(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid origin: {value!r}")
    try:
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        raise ValueError(f"Invalid origin: {value!r}") from exc
    if (
        not hostname
        or "*" in parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"Origins must not include paths, credentials, queries, or fragments: {value!r}")
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    app_name: str = "Ayman Naeem Portfolio API"
    database_url: str = "sqlite+aiosqlite:///./portfolio.db"
    database_pool_size: int = Field(5, ge=1, le=50)
    database_max_overflow: int = Field(10, ge=0, le=100)
    database_pool_recycle_seconds: int = Field(1_800, ge=60)
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    api_public_url: str = "http://localhost:8000"
    trusted_hosts: str = "localhost,127.0.0.1,test,testserver"
    trust_proxy_headers: bool = False
    local_media_dir: str = "uploads"
    jwt_secret_key: str = Field(_DEVELOPMENT_JWT_SECRET, min_length=32)
    access_token_expire_minutes: int = Field(15, ge=1, le=1_440)
    refresh_token_expire_days: int = Field(7, ge=1, le=90)
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str = ""
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    max_image_upload_mb: int = Field(15, ge=1, le=50)
    max_video_upload_mb: int = Field(200, ge=1, le=500)
    max_request_attachment_mb: int = Field(10, ge=1, le=25)
    resend_api_key: str = ""
    email_from: str = "portfolio@example.com"
    email_to: str = ""
    turnstile_secret_key: str = ""
    turnstile_expected_hostnames: str = ""
    github_username: str = ""
    github_token: str = ""
    rate_limit_max_keys: int = Field(20_000, ge=100, le=1_000_000)
    log_level: Literal["debug", "info", "warning", "error", "critical"] = "info"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        return _normalize_database_url(value)

    @field_validator("frontend_url", "api_public_url")
    @classmethod
    def validate_absolute_urls(cls, value: str) -> str:
        return _normalize_origin(value)

    @property
    def cors_list(self) -> list[str]:
        origins = [_normalize_origin(value) for value in self.cors_origins.split(",") if value.strip()]
        return list(dict.fromkeys(origins))

    @property
    def trusted_host_list(self) -> list[str]:
        return [value.strip().lower() for value in self.trusted_hosts.split(",") if value.strip()]

    @property
    def turnstile_hostname_list(self) -> list[str]:
        return [value.strip().lower() for value in self.turnstile_expected_hostnames.split(",") if value.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if not self.is_production:
            return self

        problems: list[str] = []
        secret_lower = self.jwt_secret_key.lower()
        if self.jwt_secret_key == _DEVELOPMENT_JWT_SECRET or any(
            marker in secret_lower
            for marker in ("change-me", "replace-with", "example", "placeholder", "development-only")
        ):
            problems.append("JWT_SECRET_KEY must be a unique production secret")
        if not self.database_url.startswith("postgresql+asyncpg://"):
            problems.append("DATABASE_URL must use PostgreSQL in production")
        if not self.frontend_url.startswith("https://") or not self.api_public_url.startswith("https://"):
            problems.append("FRONTEND_URL and API_PUBLIC_URL must use HTTPS in production")
        if not self.cors_list or "*" in self.cors_list:
            problems.append("CORS_ORIGINS must contain exact origins and cannot use a wildcard")
        if self.frontend_url not in self.cors_list:
            problems.append("FRONTEND_URL must be included in CORS_ORIGINS")
        if not self.trusted_host_list or "*" in self.trusted_host_list:
            problems.append("TRUSTED_HOSTS must be configured without a global wildcard")
        if any("*" in host for host in self.trusted_host_list):
            problems.append("TRUSTED_HOSTS must contain exact hostnames in production")
        api_hostname = urlsplit(self.api_public_url).hostname
        if api_hostname not in self.trusted_host_list:
            problems.append("API_PUBLIC_URL hostname must be included in TRUSTED_HOSTS")
        if not self.trust_proxy_headers:
            problems.append("TRUST_PROXY_HEADERS must be enabled behind Railway")
        if not all((self.cloudinary_cloud_name, self.cloudinary_api_key, self.cloudinary_api_secret)):
            problems.append("Cloudinary credentials are required in production")
        if not self.turnstile_secret_key or not self.turnstile_hostname_list:
            problems.append("Turnstile secret and expected hostnames are required in production")
        frontend_hostname = urlsplit(self.frontend_url).hostname
        if any("*" in host for host in self.turnstile_hostname_list):
            problems.append("TURNSTILE_EXPECTED_HOSTNAMES must contain exact hostnames")
        if frontend_hostname not in self.turnstile_hostname_list:
            problems.append("FRONTEND_URL hostname must be included in TURNSTILE_EXPECTED_HOSTNAMES")
        normalized_cookie_domain = self.cookie_domain.lstrip(".").lower()
        if normalized_cookie_domain:
            if normalized_cookie_domain.endswith("railway.app"):
                problems.append("COOKIE_DOMAIN must stay blank for Railway-generated domains")
            elif not api_hostname or not (
                api_hostname == normalized_cookie_domain
                or api_hostname.endswith("." + normalized_cookie_domain)
            ):
                problems.append("COOKIE_DOMAIN must contain the API hostname")
        if problems:
            raise ValueError("Invalid production configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

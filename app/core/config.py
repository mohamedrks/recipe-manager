from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    app_name: str = "Recipe Manager API"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Database — required, no default (app won't start without it)
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT — required, no default
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # CORS (JSON array string in env: '["http://localhost:8080"]')
    cors_origins: list[str] = ["http://localhost:8080"]

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Logging
    log_level: str = "INFO"


settings = Settings()

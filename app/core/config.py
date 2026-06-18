"""Application configuration loaded from environment variables / .env file."""

from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    PROJECT_NAME: str = "KOLEGA"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    # Defaults to a local SQLite file so the app runs with zero setup
    # (no Docker / PostgreSQL needed). To use PostgreSQL instead, set
    # DATABASE_URL, e.g.
    #   DATABASE_URL=postgresql+asyncpg://kolega:kolega@localhost:5432/kolega
    DATABASE_URL: str = "sqlite+aiosqlite:///./kolega.db"

    # Security
    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Sync connection URL (used by Alembic), derived from DATABASE_URL."""
        return self.DATABASE_URL.replace("+asyncpg", "").replace(
            "+aiosqlite", ""
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_IS_SQLITE(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

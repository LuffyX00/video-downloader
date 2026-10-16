from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, overridable via env vars prefixed with YTD_ or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="YTD_", extra="ignore")

    app_name: str = "Video Downloader API"
    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173"]

    download_dir: Path = Path("downloads")
    file_ttl_seconds: int = 3600  # how long finished files are kept
    cleanup_interval_seconds: int = 300

    max_concurrent_downloads: int = Field(default=2, ge=1, le=16)
    max_active_jobs: int = Field(default=20, ge=1)  # queued + running
    max_duration_seconds: int = 4 * 3600

    allowed_hosts: list[str] = ["youtube.com", "youtu.be", "youtube-nocookie.com"]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LocalHub API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./localhub.db"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    use_openai: bool = False
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    seed_data: bool = True
    seed_locations: bool = True
    data_dir: str = "app/data"
    upload_dir: str = "uploads"
    max_upload_bytes: int = 5 * 1024 * 1024
    frontend_public_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                import json
                return json.loads(text)
            return [item.strip() for item in text.split(",") if item.strip()]
        return value

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()

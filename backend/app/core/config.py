from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fluxo Pessoal"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://fluxo:fluxo@db:5432/fluxo_pessoal"
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

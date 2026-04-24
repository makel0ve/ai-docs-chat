from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gigachat_client_secret: SecretStr
    gigachat_client_id: SecretStr
    database_url: str
    redis_url: str
    yandex_api_key: SecretStr | None = None
    yandex_folder_id: str | None = None
    ollama_url: str = "http://localhost:11434"
    llm_provider: Literal["gigachat", "yandex", "ollama"] = "gigachat"
    embedding_provider: Literal["gigachat", "yandex", "ollama"] = "gigachat"
    ollama_chat_model: str = "qwen2.5:7b"
    ollama_embed_model: str = "bge-m3"
    upload_dir: str = "/code/uploads"
    batch_size: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

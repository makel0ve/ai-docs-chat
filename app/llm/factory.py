from functools import lru_cache

from app.config import get_settings
from app.llm.base import LLMProvider
from app.llm.gigachat import GigaChatProvider
from app.llm.ollama import OllamaProvider
from app.llm.yandexgpt import YandexGPTProvider

PROVIDERS: dict[str, type[LLMProvider]] = {
    "gigachat": GigaChatProvider,
    "yandex": YandexGPTProvider,
    "ollama": OllamaProvider,
}


@lru_cache
def _make_provider(name: str) -> LLMProvider:
    return PROVIDERS[name]()


def get_llm_provider() -> LLMProvider:
    return _make_provider(get_settings().llm_provider)


def get_embedding_provider() -> LLMProvider:
    return _make_provider(get_settings().embedding_provider)

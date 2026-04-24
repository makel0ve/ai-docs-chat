from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], stream: bool = False):
        pass

    @abstractmethod
    async def embed(self, texts: list[str]):
        pass

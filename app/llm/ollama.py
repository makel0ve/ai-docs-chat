import json

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random

from app.config import get_settings
from app.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self):
        self._settings = get_settings()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _chat_request(self, messages):
        payload = {"model": "qwen2.5:7b", "messages": messages, "stream": False}
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                url=f"{self._settings.ollama_url}/api/chat", json=payload
            )
            response.raise_for_status()

            answer = response.json()
            content = answer["message"]["content"]

            return content

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _chat_stream(self, messages):
        payload = {"model": "qwen2.5:7b", "messages": messages, "stream": True}
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", url=f"{self._settings.ollama_url}/api/chat", json=payload
            ) as response:
                async for line in response.aiter_lines():
                    data = json.loads(line)

                    if data.get("done"):
                        break

                    message = data.get("message")
                    if message:
                        content = message.get("content")

                        if content:
                            yield content

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def chat(self, messages, stream=False):
        if stream:
            return self._chat_stream(messages=messages)

        if not stream:
            return await self._chat_request(messages=messages)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def embed(self, texts):
        payload = {"model": "bge-m3", "input": texts}
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                url=f"{self._settings.ollama_url}/api/embed", json=payload
            )
            response.raise_for_status()

            answer = response.json()
            embeddings = answer["embeddings"]

            return embeddings

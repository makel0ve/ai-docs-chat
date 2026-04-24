import asyncio
import json

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random

from app.config import get_settings
from app.llm.base import LLMProvider

YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1"


class YandexGPTProvider(LLMProvider):
    def __init__(self):
        self._settings = get_settings()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _chat_request(self, messages):
        headers = {
            "Content-Type": "application/json",
        }
        headers["Authorization"] = (
            f"Api-Key {self._settings.yandex_api_key.get_secret_value()}"
        )

        payload = {
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": "2000",
            },
            "messages": [{"role": m["role"], "text": m["content"]} for m in messages],
        }
        payload["modelUri"] = (
            f"gpt://{self._settings.yandex_folder_id}/yandexgpt-lite/latest"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{YANDEX_API_URL}/completion", headers=headers, json=payload
            )
            response.raise_for_status()

        answer = response.json()
        text = answer["result"]["alternatives"][0]["message"]["text"]

        return text

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _chat_stream(self, messages):
        headers = {
            "Content-Type": "application/json",
        }
        headers["Authorization"] = (
            f"Api-Key {self._settings.yandex_api_key.get_secret_value()}"
        )

        payload = {
            "completionOptions": {
                "stream": True,
                "temperature": 0.6,
                "maxTokens": "2000",
            },
            "messages": [{"role": m["role"], "text": m["content"]} for m in messages],
        }
        payload["modelUri"] = (
            f"gpt://{self._settings.yandex_folder_id}/yandexgpt-lite/latest"
        )

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                url=f"{YANDEX_API_URL}/completion",
                headers=headers,
                json=payload,
            ) as response:
                text_pass = ""
                async for line in response.aiter_lines():
                    data = json.loads(line)
                    text_current = data["result"]["alternatives"][0]["message"]["text"][
                        len(text_pass) :
                    ]
                    text_pass += text_current

                    yield text_current

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def chat(self, messages, stream=False):
        if stream:
            return self._chat_stream(messages=messages)

        else:
            return await self._chat_request(messages=messages)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _embed_one(self, text, client):
        headers = {
            "Content-Type": "application/json",
        }
        headers["Authorization"] = (
            f"Api-Key {self._settings.yandex_api_key.get_secret_value()}"
        )

        payload = dict()
        payload["modelUri"] = (
            f"emb://{self._settings.yandex_folder_id}/text-search-doc/latest"
        )
        payload["text"] = text

        response = await client.post(
            url=f"{YANDEX_API_URL}/textEmbedding", headers=headers, json=payload
        )
        response.raise_for_status()

        answer = response.json()
        embedding = answer["embedding"]

        return embedding

    async def embed(self, texts):
        async with httpx.AsyncClient() as client:
            return await asyncio.gather(*[self._embed_one(t, client) for t in texts])

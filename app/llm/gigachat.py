import base64
import json
import time
import uuid

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random

from app.config import get_settings
from app.llm.base import LLMProvider

GIGACHAT_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1"


class GigaChatProvider(LLMProvider):
    def __init__(self):
        self._access_token = None
        self._token_expires_at = 0
        self._settings = get_settings()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def get_token(self, force: bool = False):
        if force or self._token_expires_at - 60_000 <= round(time.time() * 1000):
            payload = "scope=GIGACHAT_API_PERS"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
            headers["RqUID"] = str(uuid.uuid4())
            credentials = f"{self._settings.gigachat_client_id.get_secret_value()}:{self._settings.gigachat_client_secret.get_secret_value()}"
            headers["Authorization"] = (
                f"Basic {base64.b64encode(credentials.encode()).decode()}"
            )

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    url=GIGACHAT_OAUTH_URL, headers=headers, data=payload
                )
                response.raise_for_status()

            answer = response.json()

            self._access_token = answer["access_token"]
            self._token_expires_at = answer["expires_at"]

            return answer["access_token"]

        return self._access_token

    async def _chat_stream(self, messages, force_refresh_token: bool = False):
        token = await self.get_token(force=force_refresh_token)

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        headers["Authorization"] = f"Bearer {token}"

        payload = {"model": "GigaChat", "messages": messages, "stream": True}
        async with httpx.AsyncClient(verify=False) as client:
            async with client.stream(
                "POST",
                url=f"{GIGACHAT_API_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if "data: " in line:
                        data = line.split("data: ")
                        if data[-1] == "[DONE]":
                            break

                        json_data = json.loads(data[-1])
                        content = json_data["choices"][0]["delta"].get("content")

                        if content:
                            yield content

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _chat_request(self, messages, force_refresh_token: bool = False):
        token = await self.get_token(force=force_refresh_token)

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        headers["Authorization"] = f"Bearer {token}"

        payload = {"model": "GigaChat", "messages": messages, "stream": False}
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                url=f"{GIGACHAT_API_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

        answer = response.json()
        content = answer["choices"][0]["message"]["content"]

        return content

    async def chat(self, messages, stream=False):
        try:
            if stream:
                return self._chat_stream(messages=messages, force_refresh_token=False)

            else:
                return await self._chat_request(
                    messages=messages, force_refresh_token=False
                )

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                if stream:
                    return self._chat_stream(
                        messages=messages, force_refresh_token=True
                    )

                else:
                    return await self._chat_request(
                        messages=messages, force_refresh_token=True
                    )

            raise

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random(1, 3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _embed_request(self, texts, force_refresh_token: bool = False):
        token = await self.get_token(force=force_refresh_token)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers["Authorization"] = f"Bearer {token}"
        payload = {"model": "Embeddings", "input": texts}

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                url=f"{GIGACHAT_API_URL}/embeddings", headers=headers, json=payload
            )
            response.raise_for_status()

        answer = response.json()

        sorted_data = sorted(answer["data"], key=lambda x: x["index"])
        embedding = [item["embedding"] for item in sorted_data]

        return embedding

    async def embed(self, texts):
        try:
            return await self._embed_request(texts=texts, force_refresh_token=False)

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                return await self._embed_request(texts=texts, force_refresh_token=True)
            raise

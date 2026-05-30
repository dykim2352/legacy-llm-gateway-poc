import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.providers.base import LLMProvider, LLMProviderError


class OllamaProvider(LLMProvider):
    provider_name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama is unavailable at {self.base_url}: {exc}") from exc

        data = response.json()
        return str(data.get("response", ""))

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
        }

        timeout = httpx.Timeout(self.timeout_seconds, read=None)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        chunk = self._parse_stream_line(line)
                        if chunk.get("done"):
                            break

                        token = chunk.get("response")
                        if token:
                            yield str(token)
        except httpx.HTTPError as exc:
            raise LLMProviderError(
                f"Ollama streaming is unavailable at {self.base_url}: {exc}"
            ) from exc

    @staticmethod
    def _parse_stream_line(line: str) -> dict[str, Any]:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("Ollama returned an invalid streaming chunk.") from exc

        if not isinstance(parsed, dict):
            raise LLMProviderError("Ollama returned an unexpected streaming chunk.")

        if "error" in parsed:
            raise LLMProviderError(str(parsed["error"]))

        return parsed

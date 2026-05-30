from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProviderError(Exception):
    pass


class LLMProvider(ABC):
    provider_name: str

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncIterator[str]:
        raise NotImplementedError

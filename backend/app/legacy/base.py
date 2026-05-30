from abc import ABC, abstractmethod
from typing import Any


class LegacyConnector(ABC):
    @abstractmethod
    async def fetch_context(self, query: str) -> dict[str, Any]:
        raise NotImplementedError

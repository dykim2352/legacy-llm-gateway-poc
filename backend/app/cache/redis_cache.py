import json
import logging
from typing import Any

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import settings

logger = logging.getLogger(__name__)


class AsyncRedisCache:
    def __init__(self, url: str = settings.redis_url) -> None:
        self.client = AsyncRedis.from_url(url, decode_responses=True)

    async def get_json(self, key: str) -> dict[str, Any] | None:
        raw_value = await self.client.get(key)
        if raw_value is None:
            return None
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            logger.warning("invalid_cache_json key=%s", key)
            return None
        if not isinstance(value, dict):
            return None
        return value

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        await self.client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))


class RedisCache:
    def __init__(self, url: str = settings.redis_url) -> None:
        self.client = Redis.from_url(url, decode_responses=True)

    def get_json(self, key: str) -> dict[str, Any] | None:
        raw_value = self.client.get(key)
        if raw_value is None:
            return None
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            logger.warning("invalid_cache_json key=%s", key)
            return None
        if not isinstance(value, dict):
            return None
        return value

    def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self.client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))

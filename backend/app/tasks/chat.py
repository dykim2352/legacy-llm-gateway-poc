import asyncio
import time
from typing import Any

from app.cache.redis_cache import RedisCache
from app.core.config import settings
from app.core.metrics import LLM_REQUEST_DURATION_SECONDS, LLM_REQUESTS_TOTAL
from app.legacy.context import build_prompt
from app.providers.dependencies import get_llm_provider
from app.worker import celery_app


@celery_app.task(name="app.tasks.chat.run_chat_job")
def run_chat_job(prompt: str, context: dict[str, Any], cache_key: str) -> dict[str, Any]:
    provider = get_llm_provider()
    context_copy = dict(context)
    legacy_context = str(context_copy.pop("legacy_context", ""))
    started_at = time.perf_counter()
    metric_status = "success"

    try:
        response = asyncio.run(provider.complete(build_prompt(prompt, legacy_context, context_copy)))
    except Exception:
        metric_status = "error"
        raise
    finally:
        labels = {
            "endpoint": "celery_chat_job",
            "provider": provider.provider_name,
            "status": metric_status,
        }
        LLM_REQUESTS_TOTAL.labels(**labels).inc()
        LLM_REQUEST_DURATION_SECONDS.labels(**labels).observe(time.perf_counter() - started_at)

    payload = {
        "response": response,
        "provider": provider.provider_name,
        "cache_hit": False,
        "cache_key": cache_key,
    }
    RedisCache().set_json(
        cache_key,
        {"response": response, "provider": provider.provider_name},
        ttl_seconds=settings.cache_ttl_seconds,
    )
    return payload

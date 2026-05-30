import uuid
from typing import Any, Protocol

from celery.result import AsyncResult

from app.cache.keys import build_chat_cache_key
from app.cache.redis_cache import AsyncRedisCache
from app.core.metrics import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL
from app.jobs.models import ChatJobCreateResponse, ChatJobRequest, ChatJobStatusResponse, JobStatus
from app.legacy.client import LegacyContextClient
from app.legacy.context import LegacyContextBuilder
from app.tasks.chat import run_chat_job
from app.worker import celery_app


class AsyncJsonCache(Protocol):
    async def get_json(self, key: str) -> dict[str, Any] | None:
        raise NotImplementedError


class TaskSubmitter(Protocol):
    def apply_async(self, args: list[Any], task_id: str) -> Any:
        raise NotImplementedError


class ResultBackend(Protocol):
    def store_result(self, task_id: str, result: dict[str, Any], state: str) -> Any:
        raise NotImplementedError


class ChatJobService:
    def __init__(
        self,
        cache: AsyncJsonCache | None = None,
        task_submitter: TaskSubmitter = run_chat_job,
        result_backend: ResultBackend | None = None,
        legacy_client: LegacyContextClient | None = None,
    ) -> None:
        self.cache = cache or AsyncRedisCache()
        self.task_submitter = task_submitter
        self.result_backend = result_backend or celery_app.backend
        self.legacy_client = legacy_client or LegacyContextClient()

    async def create_chat_job(self, request: ChatJobRequest) -> ChatJobCreateResponse:
        legacy_context = await LegacyContextBuilder(self.legacy_client).build_context(
            request.context_sources
        )
        merged_context = dict(request.context)
        if legacy_context:
            merged_context["legacy_context"] = legacy_context
        cache_key = build_chat_cache_key(request.prompt, merged_context)
        cached = await self.cache.get_json(cache_key)
        job_id = str(uuid.uuid4())

        if cached is not None:
            CACHE_HITS_TOTAL.inc()
            self.result_backend.store_result(
                job_id,
                {
                    "response": cached.get("response", ""),
                    "provider": cached.get("provider"),
                    "cache_hit": True,
                    "cache_key": cache_key,
                },
                state=JobStatus.SUCCESS.value,
            )
            return ChatJobCreateResponse(
                job_id=job_id,
                status=JobStatus.SUCCESS,
                cache_hit=True,
            )

        CACHE_MISSES_TOTAL.inc()
        self.task_submitter.apply_async(
            args=[request.prompt, merged_context, cache_key],
            task_id=job_id,
        )
        return ChatJobCreateResponse(job_id=job_id, status=JobStatus.PENDING, cache_hit=False)

    def get_chat_job(self, job_id: str) -> ChatJobStatusResponse:
        result = AsyncResult(job_id, app=celery_app)
        status = _normalize_status(result.status)

        if status == JobStatus.SUCCESS:
            payload = result.result if isinstance(result.result, dict) else {}
            return ChatJobStatusResponse(
                job_id=job_id,
                status=status,
                cache_hit=bool(payload.get("cache_hit", False)),
                result=payload.get("response"),
            )

        if status == JobStatus.FAILURE:
            return ChatJobStatusResponse(job_id=job_id, status=status, error=str(result.result))

        return ChatJobStatusResponse(job_id=job_id, status=status)


def get_chat_job_service() -> ChatJobService:
    return ChatJobService()


def _normalize_status(status: str) -> JobStatus:
    if status in {state.value for state in JobStatus}:
        return JobStatus(status)
    return JobStatus.PENDING

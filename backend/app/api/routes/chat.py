import json
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import AliasChoices, BaseModel, Field

from app.audit.models import AuditEventType
from app.audit.store import append_audit_log
from app.auth.dependencies import require_user_access
from app.auth.models import User
from app.core.metrics import (
    LLM_REQUEST_DURATION_SECONDS,
    LLM_REQUESTS_TOTAL,
    LLM_STREAM_TOKENS_TOTAL,
)
from app.legacy.client import LegacyContextClient, get_legacy_context_client
from app.legacy.context import LegacyContextBuilder, build_prompt
from app.legacy.models import LegacyContextSource
from app.providers.base import LLMProvider, LLMProviderError
from app.providers.dependencies import get_llm_provider

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    prompt: str = Field(
        min_length=1,
        max_length=4000,
        validation_alias=AliasChoices("prompt", "message"),
        examples=["Mock ERP order status data를 요약해줘."],
    )
    context: dict[str, Any] = Field(default_factory=dict)
    context_sources: list[LegacyContextSource] = Field(default_factory=list)


class ChatResponse(BaseModel):
    provider: str
    response: str


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(require_user_access),
    provider: LLMProvider = Depends(get_llm_provider),
    legacy_client: LegacyContextClient = Depends(get_legacy_context_client),
) -> ChatResponse:
    started_at = time.perf_counter()
    metric_status = "success"

    try:
        append_audit_log(
            AuditEventType.LLM_REQUEST,
            user=current_user,
            path="/api/v1/chat",
            success=True,
            message="LLM chat request accepted.",
            metadata={"streaming": False, "context_source_count": len(request.context_sources)},
        )
        legacy_context = await LegacyContextBuilder(legacy_client).build_context(request.context_sources)
        response = await provider.complete(
            build_prompt(request.prompt, legacy_context, request.context)
        )
    except LLMProviderError as exc:
        metric_status = "error"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    finally:
        labels = {
            "endpoint": "chat",
            "provider": provider.provider_name,
            "status": metric_status,
        }
        LLM_REQUESTS_TOTAL.labels(**labels).inc()
        LLM_REQUEST_DURATION_SECONDS.labels(**labels).observe(time.perf_counter() - started_at)

    return ChatResponse(provider=provider.provider_name, response=response)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(require_user_access),
    provider: LLMProvider = Depends(get_llm_provider),
    legacy_client: LegacyContextClient = Depends(get_legacy_context_client),
) -> StreamingResponse:
    append_audit_log(
        AuditEventType.LLM_REQUEST,
        user=current_user,
        path="/api/v1/chat/stream",
        success=True,
        message="LLM streaming chat request accepted.",
        metadata={"streaming": True, "context_source_count": len(request.context_sources)},
    )
    legacy_context = await LegacyContextBuilder(legacy_client).build_context(request.context_sources)
    return StreamingResponse(
        _stream_sse(build_prompt(request.prompt, legacy_context, request.context), provider),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


async def _stream_sse(prompt: str, provider: LLMProvider) -> AsyncIterator[str]:
    started_at = time.perf_counter()
    metric_status = "success"

    try:
        async for token in provider.stream(prompt):
            LLM_STREAM_TOKENS_TOTAL.labels(provider=provider.provider_name).inc()
            yield _sse_event("token", {"token": token})
        yield _sse_event("done", {"provider": provider.provider_name})
    except LLMProviderError as exc:
        metric_status = "error"
        yield _sse_event("error", {"message": str(exc), "provider": provider.provider_name})
    finally:
        labels = {
            "endpoint": "chat_stream",
            "provider": provider.provider_name,
            "status": metric_status,
        }
        LLM_REQUESTS_TOTAL.labels(**labels).inc()
        LLM_REQUEST_DURATION_SECONDS.labels(**labels).observe(time.perf_counter() - started_at)


def _sse_event(event: str, data: dict[str, str]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

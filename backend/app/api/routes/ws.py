import json
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from app.audit.models import AuditEventType
from app.audit.store import append_audit_log
from app.auth.jwt import decode_access_token
from app.auth.models import Role, User
from app.auth.users import get_user
from app.core.metrics import (
    LLM_REQUEST_DURATION_SECONDS,
    LLM_REQUESTS_TOTAL,
    LLM_STREAM_TOKENS_TOTAL,
    WEBSOCKET_CONNECTIONS_TOTAL,
)
from app.providers.base import LLMProvider, LLMProviderError
from app.providers.dependencies import get_llm_provider

router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/chat")
async def websocket_chat(
    websocket: WebSocket,
    provider: LLMProvider = Depends(get_llm_provider),
) -> None:
    await websocket.accept()
    WEBSOCKET_CONNECTIONS_TOTAL.labels(path="/api/v1/ws/chat").inc()

    current_user = await _authenticate_websocket(websocket)
    if current_user is None:
        return

    logger.info(
        "websocket_connected path=/api/v1/ws/chat user=%s client=%s",
        current_user.username,
        websocket.client,
    )

    try:
        while True:
            message = await websocket.receive_text()
            logger.info("websocket_message_received provider=%s", provider.provider_name)

            try:
                prompt = _extract_prompt(message)
            except ValueError as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
                await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason=str(exc))
                logger.info("websocket_closed code=%s reason=%s", status.WS_1003_UNSUPPORTED_DATA, exc)
                return

            append_audit_log(
                AuditEventType.LLM_REQUEST,
                user=current_user,
                path="/api/v1/ws/chat",
                success=True,
                message="WebSocket LLM chat request accepted.",
                metadata={"streaming": True},
            )
            should_continue = await _stream_prompt_to_websocket(prompt, provider, websocket)
            if not should_continue:
                return
    except WebSocketDisconnect as exc:
        logger.info("websocket_disconnected code=%s client=%s", exc.code, websocket.client)


async def _stream_prompt_to_websocket(
    prompt: str,
    provider: LLMProvider,
    websocket: WebSocket,
) -> bool:
    started_at = time.perf_counter()
    metric_status = "success"

    try:
        async for token in provider.stream(prompt):
            LLM_STREAM_TOKENS_TOTAL.labels(provider=provider.provider_name).inc()
            await websocket.send_json({"type": "token", "token": token})
        await websocket.send_json({"type": "done", "provider": provider.provider_name})
    except LLMProviderError as exc:
        metric_status = "error"
        message = str(exc)
        await websocket.send_json(
            {"type": "error", "message": message, "provider": provider.provider_name}
        )
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=message[:123])
        logger.info("websocket_closed code=%s reason=%s", status.WS_1011_INTERNAL_ERROR, message)
        return False
    finally:
        labels = {
            "endpoint": "ws_chat",
            "provider": provider.provider_name,
            "status": metric_status,
        }
        LLM_REQUESTS_TOTAL.labels(**labels).inc()
        LLM_REQUEST_DURATION_SECONDS.labels(**labels).observe(time.perf_counter() - started_at)

    return True


def _extract_prompt(message: str) -> str:
    try:
        decoded: Any = json.loads(message)
    except json.JSONDecodeError:
        prompt = message.strip()
    else:
        if not isinstance(decoded, dict):
            raise ValueError("WebSocket message must be plain text or a JSON object.")
        prompt_value = decoded.get("prompt", decoded.get("message"))
        if not isinstance(prompt_value, str):
            raise ValueError("JSON WebSocket message must contain a string 'prompt' or 'message' field.")
        prompt = prompt_value.strip()

    if not prompt:
        raise ValueError("Prompt must not be empty.")

    return prompt


async def _authenticate_websocket(websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token")
    authorization = websocket.headers.get("authorization")
    if token is None and authorization is not None and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    if not token:
        message = "Missing bearer token."
        _record_websocket_authz_failure(websocket, None, message)
        await _close_websocket_auth_failure(websocket, message)
        return None

    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        message = str(exc)
        _record_websocket_authz_failure(websocket, None, message)
        await _close_websocket_auth_failure(websocket, message)
        return None

    user = get_user(payload["sub"])
    if user is None or user.role not in {Role.USER, Role.ADMIN}:
        message = "User does not have permission to access this resource."
        _record_websocket_authz_failure(websocket, payload["sub"], message)
        await _close_websocket_auth_failure(websocket, message)
        return None

    return user


async def _close_websocket_auth_failure(websocket: WebSocket, message: str) -> None:
    await websocket.send_json({"type": "error", "message": message})
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=message[:123])
    logger.info("websocket_closed code=%s reason=%s", status.WS_1008_POLICY_VIOLATION, message)


def _record_websocket_authz_failure(
    websocket: WebSocket,
    username: str | None,
    message: str,
) -> None:
    append_audit_log(
        AuditEventType.AUTHZ_FAILURE,
        username=username,
        path=str(websocket.url.path),
        success=False,
        message=message,
    )

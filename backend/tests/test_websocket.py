from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.auth.jwt import create_access_token
from app.auth.models import Role, User
from app.main import create_app
from app.providers.base import LLMProvider, LLMProviderError
from app.providers.dependencies import get_llm_provider


class FakeProvider(LLMProvider):
    provider_name = "fake"

    async def complete(self, prompt: str) -> str:
        return prompt

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        yield "hello"
        yield " world"


class FailingProvider(LLMProvider):
    provider_name = "fake"

    async def complete(self, prompt: str) -> str:
        raise LLMProviderError("provider unavailable")

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        raise LLMProviderError("stream unavailable")
        yield ""


def test_websocket_chat_streams_tokens() -> None:
    app = create_app()
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()
    client = TestClient(app)

    with client.websocket_connect(_ws_url()) as websocket:
        websocket.send_json({"prompt": "ping"})

        assert websocket.receive_json() == {"type": "token", "token": "hello"}
        assert websocket.receive_json() == {"type": "token", "token": " world"}
        assert websocket.receive_json() == {"type": "done", "provider": "fake"}


def test_websocket_chat_closes_with_clear_error_when_provider_fails() -> None:
    app = create_app()
    app.dependency_overrides[get_llm_provider] = lambda: FailingProvider()
    client = TestClient(app)

    with client.websocket_connect(_ws_url()) as websocket:
        websocket.send_json({"prompt": "ping"})

        assert websocket.receive_json() == {
            "type": "error",
            "message": "stream unavailable",
            "provider": "fake",
        }

        try:
            websocket.receive_json()
        except WebSocketDisconnect as exc:
            assert exc.code == 1011
        else:
            raise AssertionError("Expected WebSocketDisconnect")


def test_websocket_chat_rejects_invalid_message() -> None:
    app = create_app()
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()
    client = TestClient(app)

    with client.websocket_connect(_ws_url()) as websocket:
        websocket.send_json({"prompt": ""})

        assert websocket.receive_json() == {"type": "error", "message": "Prompt must not be empty."}

        try:
            websocket.receive_json()
        except WebSocketDisconnect as exc:
            assert exc.code == 1003
        else:
            raise AssertionError("Expected WebSocketDisconnect")


def test_websocket_chat_rejects_missing_token() -> None:
    client = TestClient(create_app())

    try:
        with client.websocket_connect("/api/v1/ws/chat"):
            raise AssertionError("Expected WebSocketDisconnect")
    except WebSocketDisconnect as exc:
        assert exc.code == 1008


def _ws_url() -> str:
    token = create_access_token(User(username="user", role=Role.USER))
    return f"/api/v1/ws/chat?token={token}"

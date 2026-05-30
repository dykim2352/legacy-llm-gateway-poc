from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.auth.dependencies import require_user_access
from app.auth.models import Role, User
from app.main import create_app
from app.legacy.client import get_legacy_context_client
from app.legacy.models import LegacyContextSource
from app.providers.base import LLMProvider, LLMProviderError
from app.providers.dependencies import get_llm_provider


class FakeProvider(LLMProvider):
    provider_name = "fake"

    async def complete(self, prompt: str) -> str:
        return f"complete: {prompt}"

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        yield "hello"
        yield " world"


class EchoProvider(LLMProvider):
    provider_name = "echo"

    async def complete(self, prompt: str) -> str:
        return prompt

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        yield prompt


class FailingProvider(LLMProvider):
    provider_name = "fake"

    async def complete(self, prompt: str) -> str:
        raise LLMProviderError("provider unavailable")

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        raise LLMProviderError("stream unavailable")
        yield ""


class FakeLegacyClient:
    async def fetch_source(
        self,
        source: LegacyContextSource,
    ) -> tuple[dict[str, object] | None, str | None]:
        return {
            "orderId": source.id,
            "itemName": "Tactical Network Module",
            "orderStatus": "IN_PROGRESS",
        }, None


def test_chat_returns_provider_response() -> None:
    app = create_app()
    _authorize(app)
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()
    client = TestClient(app)

    response = client.post("/api/v1/chat", json={"prompt": "ping"})

    assert response.status_code == 200
    assert response.json() == {"provider": "fake", "response": "complete: ping"}


def test_chat_adds_legacy_context_to_prompt() -> None:
    app = create_app()
    _authorize(app)
    app.dependency_overrides[get_llm_provider] = lambda: EchoProvider()
    app.dependency_overrides[get_legacy_context_client] = lambda: FakeLegacyClient()
    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={
            "prompt": "Summarize risk",
            "context_sources": [{"type": "ERP_ORDER", "id": "ORD-1001"}],
        },
    )

    assert response.status_code == 200
    prompt = response.json()["response"]
    assert "Summarize risk" in prompt
    assert "[ERP_ORDER]" in prompt
    assert "orderId: ORD-1001" in prompt
    assert "itemName: Tactical Network Module" in prompt


def test_chat_adds_manual_context_to_prompt() -> None:
    app = create_app()
    _authorize(app)
    app.dependency_overrides[get_llm_provider] = lambda: EchoProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Summarize risk",
            "context": {"priority": "HIGH", "requester": "mock-user"},
        },
    )

    assert response.status_code == 200
    prompt = response.json()["response"]
    assert "[MANUAL_CONTEXT]" in prompt
    assert "priority: HIGH" in prompt
    assert "requester: mock-user" in prompt


def test_chat_returns_clear_error_when_provider_is_unavailable() -> None:
    app = create_app()
    _authorize(app)
    app.dependency_overrides[get_llm_provider] = lambda: FailingProvider()
    client = TestClient(app)

    response = client.post("/api/v1/chat", json={"prompt": "ping"})

    assert response.status_code == 503
    assert response.json()["detail"] == "provider unavailable"


def test_chat_stream_returns_sse_token_events() -> None:
    app = create_app()
    _authorize(app)
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()
    client = TestClient(app)

    response = client.post("/api/v1/chat/stream", json={"prompt": "ping"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'event: token\ndata: {"token": "hello"}' in response.text
    assert 'event: token\ndata: {"token": " world"}' in response.text
    assert 'event: done\ndata: {"provider": "fake"}' in response.text


def test_chat_stream_returns_sse_error_event() -> None:
    app = create_app()
    _authorize(app)
    app.dependency_overrides[get_llm_provider] = lambda: FailingProvider()
    client = TestClient(app)

    response = client.post("/api/v1/chat/stream", json={"prompt": "ping"})

    assert response.status_code == 200
    assert 'event: error\ndata: {"message": "stream unavailable", "provider": "fake"}' in response.text


def _authorize(app) -> None:
    app.dependency_overrides[require_user_access] = lambda: User(username="test-user", role=Role.USER)

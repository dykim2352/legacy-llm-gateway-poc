from fastapi.testclient import TestClient

from app.audit.models import AuditEventType
from app.audit.store import clear_audit_logs_for_tests
from app.jobs.models import ChatJobCreateResponse, ChatJobRequest, ChatJobStatusResponse, JobStatus
from app.jobs.service import get_chat_job_service
from app.legacy.client import get_legacy_context_client
from app.legacy.models import LegacyContextSource
from app.main import create_app
from app.providers.base import LLMProvider
from app.providers.dependencies import get_llm_provider


class FakeProvider(LLMProvider):
    provider_name = "fake"

    async def complete(self, prompt: str) -> str:
        return f"ok: {prompt}"

    async def stream(self, prompt: str):
        yield prompt


class FakeLegacyClient:
    async def fetch_source(
        self,
        source: LegacyContextSource,
    ) -> tuple[dict[str, object] | None, str | None]:
        if source.id == "ORD-404":
            return None, f"[WARN] {source.type.value} {source.id} not found"
        return {"orderId": source.id, "orderStatus": "IN_PROGRESS"}, None


class FakeJobService:
    async def create_chat_job(self, request: ChatJobRequest) -> ChatJobCreateResponse:
        return ChatJobCreateResponse(job_id="job-1", status=JobStatus.PENDING, cache_hit=False)

    def get_chat_job(self, job_id: str) -> ChatJobStatusResponse:
        return ChatJobStatusResponse(job_id=job_id, status=JobStatus.SUCCESS, result="done")


def test_login_returns_bearer_token_and_records_success() -> None:
    clear_audit_logs_for_tests()
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "user", "password": "user-pass"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["username"] == "user"
    assert body["role"] == "USER"
    assert body["access_token"]

    logs = _admin_logs(client)
    assert any(
        log["event_type"] == AuditEventType.LOGIN_SUCCESS.value and log["username"] == "user"
        for log in logs
    )


def test_login_failure_is_audited() -> None:
    clear_audit_logs_for_tests()
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "user", "password": "wrong"},
    )

    assert response.status_code == 401
    logs = _admin_logs(client)
    assert any(log["event_type"] == AuditEventType.LOGIN_FAILURE.value for log in logs)


def test_user_can_call_chat_but_cannot_read_audit_logs() -> None:
    clear_audit_logs_for_tests()
    app = create_app()
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()
    client = TestClient(app)
    user_headers = _login_headers(client, "user", "user-pass")

    chat_response = client.post(
        "/api/v1/chat",
        json={"prompt": "hello"},
        headers=user_headers,
    )
    audit_response = client.get("/api/v1/admin/audit-logs", headers=user_headers)

    assert chat_response.status_code == 200
    assert audit_response.status_code == 403

    logs = _admin_logs(client)
    assert any(log["event_type"] == AuditEventType.LLM_REQUEST.value for log in logs)
    assert any(log["event_type"] == AuditEventType.AUTHZ_FAILURE.value for log in logs)


def test_admin_can_read_audit_logs() -> None:
    clear_audit_logs_for_tests()
    client = TestClient(create_app())

    response = client.get(
        "/api/v1/admin/audit-logs",
        headers=_login_headers(client, "admin", "admin-pass"),
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_user_can_create_and_read_chat_job_with_token() -> None:
    clear_audit_logs_for_tests()
    app = create_app()
    app.dependency_overrides[get_chat_job_service] = lambda: FakeJobService()
    client = TestClient(app)
    headers = _login_headers(client, "user", "user-pass")

    create_response = client.post("/api/v1/jobs/chat", json={"prompt": "hello"}, headers=headers)
    status_response = client.get("/api/v1/jobs/job-1", headers=headers)

    assert create_response.status_code == 200
    assert create_response.json()["status"] == JobStatus.PENDING.value
    assert status_response.status_code == 200
    assert status_response.json()["status"] == JobStatus.SUCCESS.value


def test_legacy_lookup_requires_user_and_records_audit_log() -> None:
    clear_audit_logs_for_tests()
    app = create_app()
    app.dependency_overrides[get_legacy_context_client] = lambda: FakeLegacyClient()
    client = TestClient(app)

    response = client.get(
        "/api/v1/legacy/erp/orders/ORD-1001",
        headers=_login_headers(client, "user", "user-pass"),
    )

    assert response.status_code == 200
    assert response.json()["orderId"] == "ORD-1001"

    logs = _admin_logs(client)
    assert any(log["event_type"] == AuditEventType.LEGACY_LOOKUP.value for log in logs)


def test_legacy_lookup_not_found_returns_404_and_records_failure() -> None:
    clear_audit_logs_for_tests()
    app = create_app()
    app.dependency_overrides[get_legacy_context_client] = lambda: FakeLegacyClient()
    client = TestClient(app)

    response = client.get(
        "/api/v1/legacy/erp/orders/ORD-404",
        headers=_login_headers(client, "user", "user-pass"),
    )

    assert response.status_code == 404
    logs = _admin_logs(client)
    assert any(
        log["event_type"] == AuditEventType.LEGACY_LOOKUP.value and not log["success"]
        for log in logs
    )


def _login_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _admin_logs(client: TestClient) -> list[dict[str, object]]:
    response = client.get(
        "/api/v1/admin/audit-logs",
        headers=_login_headers(client, "admin", "admin-pass"),
    )
    assert response.status_code == 200
    return response.json()

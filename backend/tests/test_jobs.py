from typing import Any

from fastapi.testclient import TestClient

from app.auth.dependencies import require_user_access
from app.auth.models import Role, User
from app.cache.keys import build_chat_cache_key
from app.jobs.models import ChatJobCreateResponse, ChatJobRequest, ChatJobStatusResponse, JobStatus
from app.jobs.service import ChatJobService, get_chat_job_service
from app.main import create_app


class FakeCache:
    def __init__(self, values: dict[str, dict[str, Any]] | None = None) -> None:
        self.values = values or {}

    async def get_json(self, key: str) -> dict[str, Any] | None:
        return self.values.get(key)


class FakeTaskSubmitter:
    def __init__(self) -> None:
        self.submitted: list[dict[str, Any]] = []

    def apply_async(self, args: list[Any], task_id: str) -> None:
        self.submitted.append({"args": args, "task_id": task_id})


class FakeResultBackend:
    def __init__(self) -> None:
        self.stored: list[dict[str, Any]] = []

    def store_result(self, task_id: str, result: dict[str, Any], state: str) -> None:
        self.stored.append({"task_id": task_id, "result": result, "state": state})


class FakeJobService:
    async def create_chat_job(self, request: ChatJobRequest) -> ChatJobCreateResponse:
        return ChatJobCreateResponse(job_id="job-1", status=JobStatus.PENDING, cache_hit=False)

    def get_chat_job(self, job_id: str) -> ChatJobStatusResponse:
        return ChatJobStatusResponse(job_id=job_id, status=JobStatus.SUCCESS, result="done")


def test_chat_cache_key_is_stable_for_context_order() -> None:
    first = build_chat_cache_key("hello", {"b": 2, "a": 1})
    second = build_chat_cache_key("hello", {"a": 1, "b": 2})

    assert first == second
    assert first.startswith("llm_gateway:chat:")


def test_create_chat_job_returns_success_on_cache_hit() -> None:
    request = ChatJobRequest(prompt="hello", context={"source": "mock"})
    cache_key = build_chat_cache_key(request.prompt, request.context)
    backend = FakeResultBackend()
    submitter = FakeTaskSubmitter()
    service = ChatJobService(
        cache=FakeCache({cache_key: {"response": "cached response", "provider": "fake"}}),
        task_submitter=submitter,
        result_backend=backend,
    )

    response = _run_async(service.create_chat_job(request))

    assert response.status == JobStatus.SUCCESS
    assert response.cache_hit is True
    assert submitter.submitted == []
    assert backend.stored[0]["state"] == JobStatus.SUCCESS.value
    assert backend.stored[0]["result"]["response"] == "cached response"


def test_create_chat_job_enqueues_task_on_cache_miss() -> None:
    request = ChatJobRequest(prompt="hello", context={"source": "mock"})
    submitter = FakeTaskSubmitter()
    service = ChatJobService(
        cache=FakeCache(),
        task_submitter=submitter,
        result_backend=FakeResultBackend(),
    )

    response = _run_async(service.create_chat_job(request))

    assert response.status == JobStatus.PENDING
    assert response.cache_hit is False
    assert submitter.submitted[0]["task_id"] == response.job_id
    assert submitter.submitted[0]["args"][0] == "hello"
    assert submitter.submitted[0]["args"][1] == {"source": "mock"}


def test_jobs_api_uses_job_service() -> None:
    app = create_app()
    app.dependency_overrides[require_user_access] = lambda: User(username="test-user", role=Role.USER)
    app.dependency_overrides[get_chat_job_service] = lambda: FakeJobService()
    client = TestClient(app)

    create_response = client.post("/api/v1/jobs/chat", json={"prompt": "hello"})
    status_response = client.get("/api/v1/jobs/job-1")

    assert create_response.status_code == 200
    assert create_response.json() == {
        "job_id": "job-1",
        "status": "PENDING",
        "cache_hit": False,
    }
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "SUCCESS"
    assert status_response.json()["result"] == "done"


def _run_async(awaitable: Any) -> Any:
    import asyncio

    return asyncio.run(awaitable)

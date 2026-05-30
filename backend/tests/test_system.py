from fastapi.testclient import TestClient

from app.main import create_app


def test_health() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics() -> None:
    client = TestClient(create_app())

    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert b"python_info" in response.content
    assert b"http_requests_total" in response.content
    assert b"http_request_duration_seconds" in response.content
    assert b"llm_requests_total" in response.content
    assert b"llm_request_duration_seconds" in response.content
    assert b"cache_hits_total" in response.content
    assert b"cache_misses_total" in response.content
    assert b"audit_events_total" in response.content
    assert b"websocket_connections_total" in response.content

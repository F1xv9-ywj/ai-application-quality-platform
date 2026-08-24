import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_chat_history_idempotency_and_session_isolation(client: TestClient) -> None:
    first = client.post("/api/chat", json={"question": "退款期限？", "session_id": "a", "request_id": "same"}).json()
    duplicate = client.post("/api/chat", json={"question": "不同问题", "session_id": "a", "request_id": "same"}).json()
    client.post("/api/chat", json={"question": "客服时间？", "session_id": "b"})
    assert duplicate["cached"] is True
    assert duplicate["answer"] == first["answer"]
    assert len(client.get("/api/sessions/a").json()) == 1
    assert len(client.get("/api/sessions/b").json()) == 1


@pytest.mark.integration
def test_timeout_and_error_simulation(client: TestClient) -> None:
    timeout = client.post("/api/chat", json={"question": "slow", "simulate": "timeout", "timeout_ms": 1})
    assert timeout.status_code == 504
    assert client.post("/api/chat", json={"question": "fail", "simulate": "error"}).status_code == 503


@pytest.mark.integration
def test_dashboard_and_missing_history(client: TestClient) -> None:
    assert "EvalForge" in client.get("/").text
    assert client.get("/api/sessions/missing").status_code == 404

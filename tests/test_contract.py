import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
def test_health_contract(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "EvalForge"}


@pytest.mark.contract
@pytest.mark.parametrize(
    "payload",
    [{"question": ""}, {"question": "ok", "top_k": 0}, {"question": "ok", "simulate": "invalid"}],
)
def test_invalid_chat_parameters(client: TestClient, payload: dict[str, object]) -> None:
    assert client.post("/api/chat", json=payload).status_code == 422


@pytest.mark.contract
def test_invalid_document(client: TestClient) -> None:
    assert client.post("/api/documents", json={"id": "bad id", "title": " ", "content": ""}).status_code == 422

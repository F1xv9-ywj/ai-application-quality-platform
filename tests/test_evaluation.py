import pytest
from fastapi.testclient import TestClient


@pytest.mark.eval
def test_sample_evaluation_metrics_thresholds(client: TestClient) -> None:
    response = client.post("/api/evaluations", json={"dataset_path": "datasets/sample.jsonl"})
    assert response.status_code == 200
    result = response.json()
    assert result["synthetic"] is True
    assert result["metrics"]["pass_rate"] >= .8
    assert result["metrics"]["retrieval_recall_at_k"] >= .8
    assert result["metrics"]["error_rate"] <= .25


@pytest.mark.eval
def test_dataset_path_guard(client: TestClient) -> None:
    assert client.post("/api/evaluations", json={"dataset_path": "../secret.jsonl"}).status_code == 400

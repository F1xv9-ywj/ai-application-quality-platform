from pathlib import Path

import pytest

from evalforge.evaluation import load_jsonl, percentile
from evalforge.service import build_sample_service


@pytest.mark.unit
def test_retrieval_is_deterministic() -> None:
    service = build_sample_service()
    assert service.retrieve("退款期限", 1)[0].document_id == "refund"


@pytest.mark.unit
def test_percentile() -> None:
    assert percentile([1, 2, 3, 100], .95) == 100


@pytest.mark.unit
def test_invalid_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text("not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="line 1"):
        load_jsonl(path)

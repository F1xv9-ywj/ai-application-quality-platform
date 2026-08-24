from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class DocumentIn(BaseModel):
    id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50_000)

    @field_validator("title", "content")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    session_id: str | None = Field(default=None, min_length=1, max_length=80)
    top_k: int = Field(default=3, ge=1, le=10)
    request_id: str | None = Field(default=None, min_length=1, max_length=100)
    simulate: Literal["none", "timeout", "error"] = "none"
    timeout_ms: int = Field(default=2_000, ge=1, le=30_000)

    @field_validator("question")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class Citation(BaseModel):
    document_id: str
    title: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    session_id: str
    request_id: str
    latency_ms: float
    cached: bool = False


class Turn(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    request_id: str


class EvalRunRequest(BaseModel):
    dataset_path: str = "datasets/sample.jsonl"
    top_k: int = Field(default=3, ge=1, le=10)
    target: Literal["local", "remote"] = "local"
    base_url: str | None = None
    api_key: str | None = None
    model: str = "demo-model"


class EvalCaseResult(BaseModel):
    id: str
    dimension_results: dict[str, bool]
    passed: bool
    latency_ms: float
    error: str | None = None
    actual: dict[str, Any] = Field(default_factory=dict)


class EvalSummary(BaseModel):
    run_id: str
    dataset: str
    synthetic: bool = True
    created_at: str
    total: int
    passed: int
    metrics: dict[str, float]
    cases: list[EvalCaseResult]

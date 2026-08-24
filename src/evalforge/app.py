from __future__ import annotations

from pathlib import Path
from typing import cast

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .evaluation import EvaluationEngine
from .models import ChatRequest, ChatResponse, DocumentIn, EvalRunRequest, EvalSummary, Turn
from .reporting import write_reports
from .service import build_sample_service

PACKAGE_DIR = Path(__file__).parent
PROJECT_DIR = PACKAGE_DIR.parents[1]


def create_app() -> FastAPI:
    app = FastAPI(
        title="EvalForge",
        version="0.1.0",
        description="AI application quality engineering reference project",
    )
    app.state.service = build_sample_service()
    app.state.runs = []
    app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")

    @app.get("/", include_in_schema=False)
    async def dashboard() -> FileResponse:
        return FileResponse(PACKAGE_DIR / "static" / "index.html")

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "EvalForge"}

    @app.post("/api/documents", status_code=status.HTTP_201_CREATED)
    async def ingest(document: DocumentIn, request: Request) -> dict[str, object]:
        stored, created = request.app.state.service.ingest(document)
        return {"document": stored, "created": created}

    @app.get("/api/documents")
    async def documents(request: Request) -> list[DocumentIn]:
        return list(request.app.state.service.documents.values())

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
        return cast(ChatResponse, await request.app.state.service.chat(payload))

    @app.get("/api/sessions/{session_id}", response_model=list[Turn])
    async def history(session_id: str, request: Request) -> list[Turn]:
        return cast(list[Turn], request.app.state.service.history(session_id))

    @app.post("/api/evaluations", response_model=EvalSummary)
    async def evaluation(payload: EvalRunRequest, request: Request) -> EvalSummary:
        dataset = Path(payload.dataset_path)
        if not dataset.is_absolute():
            dataset = PROJECT_DIR / dataset
        try:
            dataset.resolve().relative_to(PROJECT_DIR.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="dataset_path must be inside project") from exc
        if not dataset.exists():
            raise HTTPException(status_code=404, detail="dataset not found")
        try:
            summary = await EvaluationEngine(request.app.state.service).run(dataset, payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        request.app.state.runs.insert(0, summary)
        write_reports(summary, PROJECT_DIR / "reports" / "latest")
        return summary

    @app.get("/api/evaluations", response_model=list[EvalSummary])
    async def runs(request: Request) -> list[EvalSummary]:
        return cast(list[EvalSummary], request.app.state.runs)

    return app


app = create_app()

from __future__ import annotations

import asyncio
import math
import re
import time
import uuid
from collections import Counter

from fastapi import HTTPException

from .models import ChatRequest, ChatResponse, Citation, DocumentIn, Turn

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", re.UNICODE)


def tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class LocalRAGService:
    """Small deterministic target used for demos and repeatable tests."""

    def __init__(self) -> None:
        self.documents: dict[str, DocumentIn] = {}
        self.sessions: dict[str, list[Turn]] = {}
        self.request_cache: dict[str, ChatResponse] = {}

    def ingest(self, document: DocumentIn) -> tuple[DocumentIn, bool]:
        created = document.id not in self.documents
        self.documents[document.id] = document
        return document, created

    def retrieve(self, query: str, top_k: int) -> list[Citation]:
        query_counts = Counter(tokens(query))
        scored: list[tuple[float, DocumentIn]] = []
        for document in self.documents.values():
            doc_counts = Counter(tokens(f"{document.title} {document.content}"))
            overlap = sum(min(count, doc_counts[token]) for token, count in query_counts.items())
            norm = math.sqrt(max(1, sum(doc_counts.values())))
            score = overlap / norm
            if score > 0:
                scored.append((score, document))
        scored.sort(key=lambda item: (-item[0], item[1].id))
        return [
            Citation(document_id=doc.id, title=doc.title, score=round(score, 4))
            for score, doc in scored[:top_k]
        ]

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if request.request_id and request.request_id in self.request_cache:
            return self.request_cache[request.request_id].model_copy(update={"cached": True})
        if request.simulate == "error":
            raise HTTPException(status_code=503, detail="simulated target failure")
        if request.simulate == "timeout":
            try:
                await asyncio.wait_for(asyncio.sleep((request.timeout_ms + 20) / 1000), request.timeout_ms / 1000)
            except TimeoutError as exc:
                raise HTTPException(status_code=504, detail="simulated target timeout") from exc

        started = time.perf_counter()
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"
        request_id = request.request_id or f"req_{uuid.uuid4().hex[:12]}"
        citations = self.retrieve(request.question, request.top_k)
        if citations:
            source = self.documents[citations[0].document_id]
            first_sentence = re.split(r"(?<=[。！？.!?])\s*", source.content)[0].strip()
            answer = f"根据《{source.title}》，{first_sentence} [{source.id}]"
        else:
            answer = "当前资料不足，无法给出有依据的答案。"
        response = ChatResponse(
            answer=answer,
            citations=citations,
            session_id=session_id,
            request_id=request_id,
            latency_ms=round((time.perf_counter() - started) * 1000, 3),
        )
        self.sessions.setdefault(session_id, []).append(
            Turn(question=request.question, answer=answer, citations=citations, request_id=request_id)
        )
        self.request_cache[request_id] = response
        return response

    def history(self, session_id: str) -> list[Turn]:
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="session not found")
        return self.sessions[session_id]


SAMPLE_DOCUMENTS = [
    DocumentIn(id="refund", title="退款政策", content="订单支付后 7 天内可以申请退款。数字商品下载后不支持退款。"),
    DocumentIn(
        id="shipping",
        title="配送说明",
        content="标准配送通常需要 3 到 5 个工作日。加急配送通常需要 1 到 2 个工作日。",
    ),
    DocumentIn(id="support", title="客服时间", content="人工客服工作时间为周一至周五 09:00 到 18:00。"),
]


def build_sample_service() -> LocalRAGService:
    service = LocalRAGService()
    for document in SAMPLE_DOCUMENTS:
        service.ingest(document)
    return service

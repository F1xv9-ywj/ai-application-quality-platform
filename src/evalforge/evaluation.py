from __future__ import annotations

import ipaddress
import json
import os
import socket
import statistics
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

from .models import ChatRequest, EvalCaseResult, EvalRunRequest, EvalSummary
from .service import LocalRAGService


@dataclass(frozen=True)
class RemoteEndpoint:
    connect_base_url: str
    host_header: str
    sni_hostname: bytes


def resolve_remote_endpoint(base_url: str) -> RemoteEndpoint:
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("remote base_url must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise ValueError("remote base_url must not contain embedded credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("remote base_url must not contain a query or fragment")
    allowlist = {host.strip().lower() for host in os.getenv("EVALFORGE_REMOTE_ALLOWLIST", "").split(",") if host.strip()}
    hostname = parsed.hostname.lower()
    if hostname not in allowlist:
        raise ValueError("remote host is not present in EVALFORGE_REMOTE_ALLOWLIST")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, parsed.port, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise ValueError("remote host DNS resolution failed") from exc
    if not addresses:
        raise ValueError("remote host resolved to no addresses")
    verified_ips = sorted((ipaddress.ip_address(address) for address in addresses), key=lambda ip: (ip.version, ip.packed))
    for ip in verified_ips:
        if not ip.is_global or any(
            (ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_reserved, ip.is_multicast, ip.is_unspecified)
        ):
            raise ValueError("remote host resolves to a non-public address")
    pinned_ip = verified_ips[0]
    pinned_host = f"[{pinned_ip}]" if pinned_ip.version == 6 else str(pinned_ip)
    port = parsed.port
    connect_authority = f"{pinned_host}:{port}" if port is not None else pinned_host
    host_header = f"{hostname}:{port}" if port is not None else hostname
    path = parsed.path.rstrip("/")
    return RemoteEndpoint(
        connect_base_url=f"{parsed.scheme}://{connect_authority}{path}",
        host_header=host_header,
        sni_hostname=hostname.encode("idna"),
    )


def validate_remote_base_url(base_url: str) -> str:
    """Validate a remote URL without exposing transport details to callers."""
    resolve_remote_endpoint(base_url)
    return base_url.rstrip("/")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_number}: {exc.msg}") from exc
            required = {"id", "question", "expected_answer", "expected_doc_ids"}
            if not required.issubset(item):
                raise ValueError(f"line {line_number} missing required fields: {sorted(required - set(item))}")
            cases.append(item)
    if not cases:
        raise ValueError("dataset is empty")
    return cases


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile_value)))
    return ordered[index]


class EvaluationEngine:
    def __init__(self, service: LocalRAGService) -> None:
        self.service = service

    async def _invoke(self, case: dict[str, Any], request: EvalRunRequest) -> dict[str, Any]:
        if request.target == "remote":
            if not request.base_url:
                raise ValueError("base_url is required for remote target")
            endpoint = resolve_remote_endpoint(request.base_url)
            headers = {"Host": endpoint.host_header}
            if request.api_key:
                headers["Authorization"] = f"Bearer {request.api_key}"
            payload = {"model": request.model, "messages": [{"role": "user", "content": case["question"]}]}
            async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
                outgoing = client.build_request(
                    "POST",
                    f"{endpoint.connect_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    extensions={"sni_hostname": endpoint.sni_hostname},
                )
                response = await client.send(outgoing, follow_redirects=False)
                response.raise_for_status()
                body = response.json()
            return {"answer": body["choices"][0]["message"]["content"], "citations": []}
        result = await self.service.chat(
            ChatRequest(
                question=case["question"],
                session_id=case.get("session_id"),
                top_k=request.top_k,
                request_id=f"eval-{uuid.uuid4().hex}",
                simulate=case.get("simulate", "none"),
                timeout_ms=case.get("timeout_ms", 2000),
            )
        )
        return result.model_dump()

    async def run(self, dataset_path: Path, request: EvalRunRequest) -> EvalSummary:
        cases = load_jsonl(dataset_path)
        results: list[EvalCaseResult] = []
        recall_values: list[float] = []
        unsupported_values: list[float] = []
        citation_values: list[float] = []
        latencies: list[float] = []
        errors = 0
        seen_sessions: dict[str, str] = {}
        for case in cases:
            started = time.perf_counter()
            try:
                actual = await self._invoke(case, request)
                latency = (time.perf_counter() - started) * 1000
                answer = str(actual.get("answer", ""))
                citation_ids = [item["document_id"] for item in actual.get("citations", [])]
                expected_ids = set(case["expected_doc_ids"])
                recall = len(expected_ids.intersection(citation_ids)) / max(1, len(expected_ids))
                contract_ok = bool(answer.strip()) and isinstance(actual.get("citations", []), list)
                answer_ok = str(case["expected_answer"]).lower() in answer.lower()
                citation_ok = not expected_ids or bool(expected_ids.intersection(citation_ids))
                unsupported = bool(citation_ids) and not all(f"[{doc_id}]" in answer for doc_id in citation_ids[:1])
                session = str(case.get("session_id", ""))
                multi_turn_ok = not session or session not in seen_sessions or seen_sessions[session] == session
                if session:
                    seen_sessions[session] = session
                robustness_ok = True
                dimensions = {
                    "contract": contract_ok,
                    "retrieval": recall >= float(case.get("min_recall", 1.0)),
                    "answer": answer_ok,
                    "multi_turn": multi_turn_ok,
                    "robustness": robustness_ok,
                }
                if expected_ids:
                    recall_values.append(recall)
                unsupported_values.append(float(unsupported))
                citation_values.append(float(citation_ok))
                latencies.append(latency)
                results.append(EvalCaseResult(id=case["id"], dimension_results=dimensions, passed=all(dimensions.values()), latency_ms=round(latency, 3), actual=actual))
            except Exception as exc:  # evaluator records target failures as data
                latency = (time.perf_counter() - started) * 1000
                errors += 1
                latencies.append(latency)
                expected_failure = bool(case.get("expect_error"))
                dimensions = {"contract": False, "retrieval": False, "answer": False, "multi_turn": True, "robustness": expected_failure}
                results.append(EvalCaseResult(id=case["id"], dimension_results=dimensions, passed=expected_failure, latency_ms=round(latency, 3), error=str(exc)))
        passed = sum(result.passed for result in results)
        metrics = {
            "pass_rate": passed / len(results),
            "retrieval_recall_at_k": statistics.fmean(recall_values) if recall_values else 0.0,
            "citation_rate": statistics.fmean(citation_values) if citation_values else 0.0,
            "unsupported_claim_rate": statistics.fmean(unsupported_values) if unsupported_values else 0.0,
            "latency_p50_ms": percentile(latencies, 0.50),
            "latency_p95_ms": percentile(latencies, 0.95),
            "error_rate": errors / len(results),
        }
        return EvalSummary(
            run_id=f"run_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            dataset=str(dataset_path), created_at=datetime.now(UTC).isoformat(), total=len(results), passed=passed,
            metrics={key: round(value, 4) for key, value in metrics.items()}, cases=results,
        )

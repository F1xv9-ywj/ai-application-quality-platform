import socket

import httpx
import pytest

from evalforge.evaluation import EvaluationEngine, resolve_remote_endpoint, validate_remote_base_url
from evalforge.models import EvalRunRequest
from evalforge.service import build_sample_service


@pytest.mark.unit
@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "https://user:pass@example.com/v1", "https://not-allowed.example/v1"],
)
def test_remote_url_rejects_invalid_or_unlisted_hosts(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    monkeypatch.setenv("EVALFORGE_REMOTE_ALLOWLIST", "example.com")
    with pytest.raises(ValueError):
        validate_remote_base_url(url)


@pytest.mark.unit
@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "224.0.0.1"])
def test_remote_url_rejects_non_public_dns(monkeypatch: pytest.MonkeyPatch, address: str) -> None:
    monkeypatch.setenv("EVALFORGE_REMOTE_ALLOWLIST", "example.com")
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(socket.AF_INET, 0, 0, "", (address, 443))])
    with pytest.raises(ValueError, match="non-public"):
        validate_remote_base_url("https://example.com/v1")


@pytest.mark.unit
def test_remote_url_accepts_allowlisted_public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVALFORGE_REMOTE_ALLOWLIST", "api.example.com")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, 0, 0, "", ("93.184.216.34", 443))],
    )
    assert validate_remote_base_url("https://api.example.com/v1") == "https://api.example.com/v1"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("base_url", "expected_connect", "expected_host", "expected_sni"),
    [
        ("https://api.example.com/v1", "https://93.184.216.34/v1", "api.example.com", b"api.example.com"),
        ("http://api.example.com:8080/custom", "http://93.184.216.34:8080/custom", "api.example.com:8080", b"api.example.com"),
    ],
)
def test_resolution_pins_transport_ip_and_preserves_host_sni(
    monkeypatch: pytest.MonkeyPatch,
    base_url: str,
    expected_connect: str,
    expected_host: str,
    expected_sni: bytes,
) -> None:
    calls = 0

    def fake_getaddrinfo(*args: object, **kwargs: object) -> list[tuple[object, ...]]:
        nonlocal calls
        calls += 1
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    monkeypatch.setenv("EVALFORGE_REMOTE_ALLOWLIST", "api.example.com")
    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    endpoint = resolve_remote_endpoint(base_url)
    assert endpoint.connect_base_url == expected_connect
    assert endpoint.host_header == expected_host
    assert endpoint.sni_hostname == expected_sni
    assert calls == 1


@pytest.mark.unit
@pytest.mark.anyio
@pytest.mark.parametrize(
    ("base_url", "expected_url", "expected_host"),
    [
        ("https://api.example.com/v1", "https://93.184.216.34/v1/chat/completions", "api.example.com"),
        ("http://api.example.com:8080/v1", "http://93.184.216.34:8080/v1/chat/completions", "api.example.com:8080"),
    ],
)
async def test_remote_invoke_sends_to_pinned_ip_without_second_dns(
    monkeypatch: pytest.MonkeyPatch,
    base_url: str,
    expected_url: str,
    expected_host: str,
) -> None:
    dns_calls = 0
    sent: list[httpx.Request] = []

    def fake_getaddrinfo(*args: object, **kwargs: object) -> list[tuple[object, ...]]:
        nonlocal dns_calls
        dns_calls += 1
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            assert kwargs["follow_redirects"] is False

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        def build_request(self, *args: object, **kwargs: object) -> httpx.Request:
            return httpx.Request(*args, **kwargs)

        async def send(self, request: httpx.Request, **kwargs: object) -> httpx.Response:
            assert kwargs["follow_redirects"] is False
            sent.append(request)
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "grounded answer"}}]},
                request=request,
            )

    monkeypatch.setenv("EVALFORGE_REMOTE_ALLOWLIST", "api.example.com")
    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    engine = EvaluationEngine(build_sample_service())
    result = await engine._invoke(
        {"question": "test"},
        EvalRunRequest(target="remote", base_url=base_url, model="test-model"),
    )
    assert result["answer"] == "grounded answer"
    assert dns_calls == 1
    assert len(sent) == 1
    assert str(sent[0].url) == expected_url
    assert sent[0].headers["host"] == expected_host
    assert sent[0].extensions["sni_hostname"] == b"api.example.com"

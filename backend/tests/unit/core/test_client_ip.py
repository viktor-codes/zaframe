"""Unit tests for trusted-proxy client IP extraction."""

import pytest
from starlette.requests import Request

from app.core.client_ip import (
    get_client_ip_for_rate_limit,
    parse_trusted_proxy_networks,
)
from app.core.config import settings


def _request(*, client_host: str, x_forwarded_for: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if x_forwarded_for is not None:
        headers.append((b"x-forwarded-for", x_forwarded_for.encode("latin-1")))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": headers,
        "client": (client_host, 12345),
        "server": ("test", 80),
    }
    return Request(scope)


def test_parse_trusted_proxy_networks_accepts_ip_and_cidr() -> None:
    nets = parse_trusted_proxy_networks("127.0.0.1, 10.0.0.0/8, not-an-ip")
    assert len(nets) == 2


def test_untrusted_peer_ignores_spoofed_xff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "TRUSTED_PROXY_IPS", "10.0.0.0/8")
    request = _request(
        client_host="203.0.113.9",
        x_forwarded_for="198.51.100.1",
    )
    assert get_client_ip_for_rate_limit(request) == "203.0.113.9"


def test_trusted_peer_uses_leftmost_xff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "TRUSTED_PROXY_IPS", "10.0.0.0/8")
    request = _request(
        client_host="10.0.0.5",
        x_forwarded_for="198.51.100.1, 10.0.0.5",
    )
    assert get_client_ip_for_rate_limit(request) == "198.51.100.1"


def test_empty_trusted_list_never_reads_xff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "TRUSTED_PROXY_IPS", "")
    request = _request(
        client_host="10.0.0.5",
        x_forwarded_for="198.51.100.1",
    )
    assert get_client_ip_for_rate_limit(request) == "10.0.0.5"


def test_trusted_peer_without_xff_falls_back_to_peer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "TRUSTED_PROXY_IPS", "127.0.0.1")
    request = _request(client_host="127.0.0.1")
    assert get_client_ip_for_rate_limit(request) == "127.0.0.1"

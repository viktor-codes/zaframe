"""
Client IP extraction for rate limiting behind reverse proxies.

X-Forwarded-For is only trusted when the immediate peer (request.client.host)
is listed in TRUSTED_PROXY_IPS. Otherwise spoofed XFF headers are ignored.
"""

from __future__ import annotations

from ipaddress import IPv4Network, IPv6Network, ip_address, ip_network
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request

from app.core.config import settings

TrustedNetwork = IPv4Network | IPv6Network


def parse_trusted_proxy_networks(raw: str) -> tuple[TrustedNetwork, ...]:
    """Parse comma-separated IPs/CIDRs into ip_network objects."""
    networks: list[TrustedNetwork] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            if "/" in token:
                networks.append(ip_network(token, strict=False))
            else:
                addr = ip_address(token)
                networks.append(
                    ip_network(f"{addr}/{addr.max_prefixlen}", strict=False)
                )
        except ValueError:
            continue
    return tuple(networks)


def _peer_host(request: Request) -> str:
    if request.client is None or not request.client.host:
        return "127.0.0.1"
    return request.client.host


def _peer_is_trusted(peer: str, networks: tuple[TrustedNetwork, ...]) -> bool:
    if not networks:
        return False
    try:
        addr = ip_address(peer)
    except ValueError:
        return False
    return any(addr in net for net in networks)


def _leftmost_forwarded_for(header_value: str) -> str | None:
    """Return the original client IP (leftmost) from X-Forwarded-For."""
    first = header_value.split(",")[0].strip()
    if not first:
        return None
    try:
        ip_address(first)
    except ValueError:
        return None
    return first


def get_client_ip_for_rate_limit(request: Request) -> str:
    """
    IP key for SlowAPI limits.

    When the peer is a trusted proxy, use the leftmost X-Forwarded-For hop
    (client as seen by a single edge LB). Otherwise use the peer address only.
    """
    peer = _peer_host(request)
    networks = parse_trusted_proxy_networks(settings.TRUSTED_PROXY_IPS)
    if not _peer_is_trusted(peer, networks):
        return peer

    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return peer
    client = _leftmost_forwarded_for(forwarded)
    return client if client is not None else peer

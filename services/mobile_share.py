from __future__ import annotations

from ipaddress import ip_address
import socket
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

DEFAULT_MOBILE_PORT = 8765
DEFAULT_MOBILE_PATH = "/mobile"
DEFAULT_HEALTH_PATH = "/health"


def build_mobile_share_url(host: str, port: int = DEFAULT_MOBILE_PORT) -> str:
    return f"http://{host}:{port}{DEFAULT_MOBILE_PATH}"


def detect_local_network_ip() -> str | None:
    candidates: list[str] = []
    candidates.extend(_udp_candidates())
    candidates.extend(_hostname_candidates())
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if _is_valid_network_ip(candidate):
            return candidate
    return None


def is_mobile_backend_reachable(host: str, port: int = DEFAULT_MOBILE_PORT, timeout: float = 0.8) -> bool:
    target = f"http://{host}:{port}{DEFAULT_HEALTH_PATH}"
    try:
        with urlopen(target, timeout=timeout) as response:
            return response.status == 200
    except (HTTPError, URLError, TimeoutError, OSError):
        return False


def _udp_candidates() -> list[str]:
    candidates: list[str] = []
    for target in (("8.8.8.8", 80), ("1.1.1.1", 80), ("192.168.0.1", 80)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(target)
                candidates.append(sock.getsockname()[0])
        except OSError:
            continue
    return candidates


def _hostname_candidates() -> list[str]:
    candidates: list[str] = []
    try:
        _, _, addresses = socket.gethostbyname_ex(socket.gethostname())
        candidates.extend(addresses)
    except OSError:
        pass
    try:
        infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM)
        candidates.extend(info[4][0] for info in infos if info[4])
    except OSError:
        pass
    return candidates


def _is_valid_network_ip(value: str) -> bool:
    try:
        ip = ip_address(value)
    except ValueError:
        return False
    return bool(
        ip.version == 4
        and not ip.is_loopback
        and not ip.is_link_local
        and not ip.is_unspecified
        and ip.is_private
    )

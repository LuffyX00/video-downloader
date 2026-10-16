from urllib.parse import urlparse

from app.exceptions import InvalidUrlError


def is_allowed_url(url: str, allowed_hosts: list[str]) -> bool:
    """True if `url` is http(s) and its host is (a subdomain of) an allowed host."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    return any(host == h or host.endswith(f".{h}") for h in allowed_hosts)


def ensure_allowed_url(url: str, allowed_hosts: list[str]) -> None:
    if not is_allowed_url(url, allowed_hosts):
        raise InvalidUrlError()

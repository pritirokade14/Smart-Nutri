from types import SimpleNamespace

from app.core.config import Settings
from app.core.ratelimit import client_ip


def _req(xff: str | None, host: str | None = "10.0.0.1"):
    headers = {} if xff is None else {"x-forwarded-for": xff}
    client = SimpleNamespace(host=host) if host else None
    return SimpleNamespace(headers=headers, client=client)


def _s(hops: int) -> Settings:
    return Settings(_env_file=None, trusted_proxy_hops=hops)


def test_hops_zero_ignores_header():
    assert client_ip(_req("1.1.1.1"), _s(0)) == "10.0.0.1"


def test_hops_one_takes_rightmost():
    assert client_ip(_req("9.9.9.9, 1.1.1.1"), _s(1)) == "1.1.1.1"


def test_hops_two_takes_second_from_right():
    assert client_ip(_req("9.9.9.9, 1.1.1.1, 35.0.0.1"), _s(2)) == "1.1.1.1"


def test_spoofed_left_entries_ignored():
    assert client_ip(_req("6.6.6.6, 7.7.7.7, 1.1.1.1, 35.0.0.1"), _s(2)) == "1.1.1.1"


def test_missing_header_falls_back():
    assert client_ip(_req(None), _s(1)) == "10.0.0.1"


def test_short_header_falls_back():
    assert client_ip(_req("1.1.1.1"), _s(2)) == "10.0.0.1"


def test_no_client_unknown():
    assert client_ip(_req(None, host=None), _s(1)) == "unknown"

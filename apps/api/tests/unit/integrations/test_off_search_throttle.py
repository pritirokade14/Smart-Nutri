"""I4: a process-wide token bucket on Open Food Facts search calls (OFF allows about 10
search requests a minute per client; we stay at 8)."""

import httpx
import pytest

from app.core.config import Settings
from app.integrations.openfoodfacts import (
    OffClient,
    OffThrottled,
    OffUnavailable,
    SearchThrottle,
)


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_default_is_8_searches_a_minute():
    assert Settings(_env_file=None).off_search_per_minute == 8


def test_bucket_allows_a_burst_then_refills_one_token_every_7_5_s():
    clock = Clock()
    bucket = SearchThrottle(8, clock=clock)
    assert [bucket.try_acquire() for _ in range(9)] == [True] * 8 + [False]
    assert bucket.retry_after() == 8  # 7.5 s, rounded up
    clock.now += 7.4
    assert not bucket.try_acquire()
    clock.now += 0.1
    assert bucket.try_acquire()
    assert not bucket.try_acquire()
    clock.now += 600  # never more than a minute's worth saved up
    assert [bucket.try_acquire() for _ in range(9)] == [True] * 8 + [False]


def test_throttled_is_an_off_outage():
    # Callers that already handle OffUnavailable (stale cache, 503) handle it too.
    assert issubclass(OffThrottled, OffUnavailable)


def _client(throttle: SearchThrottle) -> tuple[OffClient, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"products": []})

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = OffClient(
        http, base_url="https://off.test", user_agent="T/1", search_throttle=throttle
    )
    return client, seen


async def test_client_refuses_searches_over_the_limit_without_calling_off():
    clock = Clock()
    client, seen = _client(SearchThrottle(2, clock=clock))
    assert await client.search_text("namkeen") == []
    assert await client.search_by_category("en:snacks") == []  # same bucket
    with pytest.raises(OffThrottled) as err:
        await client.search_text("biscuit")
    assert err.value.retry_after == 30
    assert len(seen) == 2


async def test_product_lookups_are_not_throttled():
    client, seen = _client(SearchThrottle(1, clock=Clock()))

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if "/search" in request.url.path:
            return httpx.Response(200, json={"products": []})
        return httpx.Response(200, json={"status": "success", "product": {"code": "1"}})

    client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    await client.search_text("namkeen")
    for _ in range(3):
        assert await client.get_product("8901234567890") == {"code": "1"}
    assert len(seen) == 4

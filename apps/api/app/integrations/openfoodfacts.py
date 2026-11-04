"""Open Food Facts v3 client.

API docs: https://openfoodfacts.github.io/openfoodfacts-server/api/
Verified against the live API: an unknown barcode returns HTTP 404 with
`{"status": "failure", "result": {"id": "product_not_found"}, ...}`; a hit returns
HTTP 200 with `{"status": "success", "product": {...}}`.

OFF data is ODbL: every call sends a User-Agent. No retries here (the service decides).
Logs carry outcome and latency only, never the barcode.
"""

import logging
import math
import re
import time
from collections.abc import Callable

import httpx
from fastapi import Request

logger = logging.getLogger(__name__)

# Must cover every field off_mapping.py reads (a test enforces this): a missing field would
# silently drop allergen or nutrient data.
PRODUCT_FIELDS = (
    "code,product_name,brands,image_front_url,image_url,categories_tags,nutriments,"
    "serving_quantity,serving_quantity_unit,ingredients_text,ingredients_text_en,"
    "ingredients_text_hi,ingredients_text_mr,ingredients_lc,lang,additives_tags,"
    "nutrition_data_per,serving_size,allergens_tags,traces_tags,labels_tags"
)
# Sent when OFF_USER_AGENT is blank or still the .env.example placeholder (OFF requires a real UA).
DEFAULT_USER_AGENT = "SmartNutri/0.1 (+https://github.com/pritirokade14/Smart-Nutri)"
_TIMEOUT = httpx.Timeout(5.0, connect=3.0)
_NOT_FOUND_IDS = {"product_not_found"}


class InvalidBarcode(ValueError):
    pass


class OffUnavailable(Exception):
    """Network error, timeout, 5xx, or malformed body."""


class OffThrottled(OffUnavailable):
    """Our own OFF search budget is used up (I4); OFF was not called. `retry_after` is the
    number of seconds until the next search is allowed."""

    def __init__(self, retry_after: int) -> None:
        super().__init__("off search throttled")
        self.retry_after = retry_after


class SearchThrottle:
    """A token bucket for OFF search calls, shared by the whole process (one per app, kept on
    `app.state`). Holds at most a minute's worth of tokens and refills continuously.

    Single event loop, no await inside: safe without a lock.
    """

    def __init__(self, per_minute: int, *, clock: Callable[[], float] = time.monotonic) -> None:
        if per_minute < 1:
            raise ValueError("per_minute must be at least 1")
        self._capacity = float(per_minute)
        self._rate = per_minute / 60.0  # tokens per second
        self._clock = clock
        self._tokens = self._capacity
        self._updated = clock()

    def _refill(self) -> None:
        now = self._clock()
        self._tokens = min(self._capacity, self._tokens + (now - self._updated) * self._rate)
        self._updated = now

    def try_acquire(self) -> bool:
        self._refill()
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

    def retry_after(self) -> int:
        """Whole seconds until a token is available (at least 1)."""
        self._refill()
        return max(1, math.ceil((1.0 - self._tokens) / self._rate))


# EAN-8, UPC-A, EAN-13, GTIN-14 (Plan 3 global constraint; same rule on Android and web).
VALID_LENGTHS = frozenset({8, 12, 13, 14})


def normalize_barcode(raw: str) -> str:
    cleaned = re.sub(r"[\s-]+", "", raw or "")
    if not cleaned.isascii() or not cleaned.isdigit() or len(cleaned) not in VALID_LENGTHS:
        raise InvalidBarcode("barcode must be 8, 12, 13 or 14 digits")
    return cleaned


def get_off_client(request: Request) -> "OffClient":
    """FastAPI dependency: an OffClient over the app's shared httpx client (see create_app)."""
    settings = request.app.state.settings
    return OffClient(
        request.app.state.off_http,
        base_url=settings.off_base_url,
        user_agent=settings.off_user_agent,
        search_throttle=request.app.state.off_search_throttle,
    )


class OffClient:
    def __init__(
        self,
        http: httpx.AsyncClient,
        *,
        base_url: str,
        user_agent: str,
        search_throttle: SearchThrottle | None = None,
    ) -> None:
        self._http = http
        self._search_throttle = search_throttle
        self._base_url = base_url.rstrip("/")
        ua = (user_agent or "").strip()
        self._user_agent = DEFAULT_USER_AGENT if not ua or "your-team-email@" in ua else ua

    async def get_product(self, barcode: str) -> dict | None:
        """Return OFF's v3 product object, None when OFF has no such product.

        The injected httpx client is owned (and closed) by the caller, e.g. the app lifespan.
        """
        barcode = normalize_barcode(barcode)  # never interpolate unvalidated input into the path
        url = f"{self._base_url}/api/v3/product/{barcode}"
        start = time.monotonic()
        outcome = "unavailable"
        try:
            try:
                resp = await self._http.get(
                    url,
                    params={"fields": PRODUCT_FIELDS},
                    headers={"User-Agent": self._user_agent},
                    timeout=_TIMEOUT,
                )
            except httpx.HTTPError as exc:
                raise OffUnavailable("off request failed") from exc

            if resp.status_code >= 500:
                raise OffUnavailable("off server error")
            try:
                body = resp.json()
            except ValueError as exc:
                if resp.status_code == 404:
                    outcome = "not_found"
                    return None
                raise OffUnavailable("off returned invalid json") from exc

            if resp.status_code == 404:
                outcome = "not_found"
                return None
            if resp.status_code != 200 or not isinstance(body, dict):
                raise OffUnavailable("off unexpected response")

            if body.get("status") == "failure":
                result = body.get("result")
                if isinstance(result, dict) and result.get("id") in _NOT_FOUND_IDS:
                    outcome = "not_found"
                    return None
                raise OffUnavailable("off reported failure")

            product = body.get("product")
            if not isinstance(product, dict):
                raise OffUnavailable("off body missing product")
            outcome = "found"
            return product
        finally:
            logger.info(
                "off_lookup outcome=%s latency_ms=%d", outcome, (time.monotonic() - start) * 1000
            )

    async def search_by_category(self, category_tag: str, page_size: int = 24) -> list[dict]:
        """Products in one OFF category (v2 search), with the same fields as ``get_product``.

        Callers cache the result (``off_product_cache``, >= 24 h): OFF limits search requests.
        """
        return await self._search(
            "/api/v2/search",
            {"categories_tags": category_tag, "page_size": str(page_size)},
            kind="category",
        )

    async def search_text(self, query: str, page_size: int = 20) -> list[dict]:
        """Full-text product search (the OFF search endpoint; v2 has no text search)."""
        return await self._search(
            "/cgi/search.pl",
            {
                "search_terms": query,
                "search_simple": "1",
                "action": "process",
                "json": "1",
                "page_size": str(page_size),
            },
            kind="text",
        )

    async def _search(self, path: str, params: dict[str, str], *, kind: str) -> list[dict]:
        """GET a search endpoint; the ``products`` list (objects only). Logs never carry the
        query, only the outcome, count and latency. Raises OffThrottled, without calling OFF,
        when the process-wide search budget is used up (I4)."""
        if self._search_throttle is not None and not self._search_throttle.try_acquire():
            logger.info("off_search kind=%s outcome=throttled", kind)
            raise OffThrottled(self._search_throttle.retry_after())
        start = time.monotonic()
        outcome = "unavailable"
        try:
            try:
                resp = await self._http.get(
                    f"{self._base_url}{path}",
                    params={**params, "fields": PRODUCT_FIELDS},
                    headers={"User-Agent": self._user_agent},
                    timeout=_TIMEOUT,
                )
            except httpx.HTTPError as exc:
                raise OffUnavailable("off search failed") from exc
            if resp.status_code != 200:
                raise OffUnavailable("off search unexpected status")
            try:
                body = resp.json()
            except ValueError as exc:
                raise OffUnavailable("off search returned invalid json") from exc
            products = body.get("products") if isinstance(body, dict) else None
            if not isinstance(products, list):
                raise OffUnavailable("off search body missing products")
            found = [p for p in products if isinstance(p, dict)]
            outcome = f"found:{len(found)}"
            return found
        finally:
            logger.info(
                "off_search kind=%s outcome=%s latency_ms=%d",
                kind,
                outcome,
                (time.monotonic() - start) * 1000,
            )

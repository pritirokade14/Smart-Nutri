"""Open Food Facts v3 client.

API docs: https://openfoodfacts.github.io/openfoodfacts-server/api/
Verified against the live API: an unknown barcode returns HTTP 404 with
`{"status": "failure", "result": {"id": "product_not_found"}, ...}`; a hit returns
HTTP 200 with `{"status": "success", "product": {...}}`.

OFF data is ODbL: every call sends a User-Agent. No retries here (the service decides).
Logs carry outcome and latency only, never the barcode.
"""

import logging
import re
import time

import httpx

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


# EAN-8, UPC-A, EAN-13, GTIN-14 (Plan 3 global constraint; same rule on Android and web).
VALID_LENGTHS = frozenset({8, 12, 13, 14})


def normalize_barcode(raw: str) -> str:
    cleaned = re.sub(r"[\s-]+", "", raw or "")
    if not cleaned.isascii() or not cleaned.isdigit() or len(cleaned) not in VALID_LENGTHS:
        raise InvalidBarcode("barcode must be 8, 12, 13 or 14 digits")
    return cleaned


class OffClient:
    def __init__(self, http: httpx.AsyncClient, *, base_url: str, user_agent: str) -> None:
        self._http = http
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

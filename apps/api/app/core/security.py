"""Supabase access-token verification.

Tokens are verified against the project's JWKS (asymmetric keys only). Every failure is
reported as a generic 401 through the error envelope; details go to logs, never to clients.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated, Any
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_app_settings
from app.core.errors import ApiError

logger = logging.getLogger(__name__)

ALLOWED_ALGORITHMS = frozenset({"ES256", "RS256"})
AUDIENCE = "authenticated"
LEEWAY_SECONDS = 30
MAX_STALE_SECONDS = 86_400  # hard cap on serving last-good keys after failed refreshes
MAX_TOKEN_LENGTH = 8192
_ASYMMETRIC_KTY = frozenset({"EC", "RSA"})

# OpenAPI: components.securitySchemes.bearerAuth plus per-operation `security`, so the
# generated clients carry no `authorization` parameter (their interceptors set the header).
# auto_error=False: a missing/non-Bearer header returns None and we raise our own envelope.
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


@dataclass(frozen=True, slots=True)
class AccountContext:
    account_id: UUID
    email: str | None


def _auth_required() -> ApiError:
    return ApiError("auth_required", 401, headers={"WWW-Authenticate": "Bearer"})


def _auth_invalid() -> ApiError:
    return ApiError(
        "auth_invalid", 401, headers={"WWW-Authenticate": 'Bearer error="invalid_token"'}
    )


def auth_invalid_error() -> ApiError:
    """The 401 `auth_invalid` error, for a verified token that must still be refused (an
    erased account's token, ruling D1/B1)."""
    return _auth_invalid()


async def _http_fetch(url: str) -> dict:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def _parse_jwks(doc: Any) -> dict[str, jwt.PyJWK]:
    """Keep only usable asymmetric signing keys with a kid and an allowed algorithm."""
    if not isinstance(doc, dict) or not isinstance(doc.get("keys"), list):
        raise TypeError("malformed JWKS document")
    keys: dict[str, jwt.PyJWK] = {}
    for entry in doc["keys"]:
        if not isinstance(entry, dict):
            continue
        kid = entry.get("kid")
        if not isinstance(kid, str) or not kid:
            continue
        if entry.get("kty") not in _ASYMMETRIC_KTY or entry.get("use", "sig") != "sig":
            continue
        try:
            key = jwt.PyJWK(entry)
        except jwt.PyJWTError:
            continue
        key_ops = entry.get("key_ops")
        if key_ops is not None and (not isinstance(key_ops, list) or "verify" not in key_ops):
            continue
        if key.algorithm_name in ALLOWED_ALGORITHMS:
            keys[kid] = key
    return keys


class JwksCache:
    # Minimum gap between refetches triggered by an unknown kid, and the retry backoff
    # after a failed fetch. Stops a flood of random kids from becoming a flood of fetches.
    _MIN_REFETCH_SECONDS = 10.0

    def __init__(
        self,
        jwks_url: str,
        ttl_seconds: int = 600,
        fetch: Callable[[str], Awaitable[dict]] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._jwks_url = jwks_url
        self._ttl = ttl_seconds
        self._fetch = fetch or _http_fetch
        self._clock = clock
        self._keys: dict[str, jwt.PyJWK] = {}
        self._expires_at: float | None = None
        self._last_success: float | None = None
        self._last_forced: float | None = None
        # One cache (and lock) per app instance, which runs on one event loop per worker.
        self._lock = asyncio.Lock()

    async def key_for(self, kid: str) -> jwt.PyJWK:
        async with self._lock:
            now = self._clock()
            refreshed = False
            if self._expires_at is None or now >= self._expires_at:
                await self._refresh(now)
                refreshed = True
            key = self._keys.get(kid)
            if key is None and not refreshed and self._may_force(now):
                self._last_forced = now
                await self._refresh(now)
                key = self._keys.get(kid)
        if key is None:
            raise _auth_invalid()
        return key

    def _may_force(self, now: float) -> bool:
        return self._last_forced is None or now - self._last_forced >= self._MIN_REFETCH_SECONDS

    async def _refresh(self, now: float) -> None:
        try:
            keys = _parse_jwks(await self._fetch(self._jwks_url))
        except Exception as exc:  # noqa: BLE001 - any fetch/parse failure must become a 401
            # Keep the last good keys and retry after a short backoff.
            logger.warning("jwks refresh failed: %s", type(exc).__name__)
            self._expires_at = now + self._MIN_REFETCH_SECONDS
            if self._last_success is None or now - self._last_success > MAX_STALE_SECONDS:
                # Fail closed: the last-good keys are too old to trust.
                self._keys = {}
                logger.error("jwks refresh failing and last-good keys exceed the staleness cap")
            return
        self._keys = keys
        self._last_success = now
        self._expires_at = now + self._ttl


def get_jwks_cache(request: Request) -> JwksCache:
    """The app's JWKS cache, built by `create_app()` from its Settings."""
    return request.app.state.jwks_cache


async def current_account(
    jwks: Annotated[JwksCache, Depends(get_jwks_cache)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)] = None,
) -> AccountContext:
    # bearer_scheme returns None for a missing header, a non-Bearer scheme or an empty token.
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _auth_required()
    token = credentials.credentials.strip()
    if not token:
        raise _auth_required()
    if len(token) > MAX_TOKEN_LENGTH:
        raise _auth_invalid()

    if not settings.supabase_url:
        logger.error("SUPABASE_URL is not configured; rejecting token")
        raise _auth_invalid()

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise _auth_invalid() from None
    alg = header.get("alg")
    kid = header.get("kid")
    if (
        not isinstance(alg, str)
        or alg not in ALLOWED_ALGORITHMS
        or not isinstance(kid, str)
        or not kid
    ):
        raise _auth_invalid()

    key = await jwks.key_for(kid)
    if key.algorithm_name != alg:
        raise _auth_invalid()

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience=AUDIENCE,
            issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
            leeway=LEEWAY_SECONDS,
            options={"require": ["exp", "aud", "iss", "sub"]},
        )
    except jwt.PyJWTError as exc:
        logger.info("rejected access token: %s", type(exc).__name__)
        raise _auth_invalid() from None

    if claims.get("role") != "authenticated" or claims.get("is_anonymous") is True:
        raise _auth_invalid()

    sub = claims.get("sub")
    try:
        account_id = UUID(sub) if isinstance(sub, str) else None
    except ValueError:
        account_id = None
    if account_id is None or str(account_id) != sub:
        raise _auth_invalid()

    email = claims.get("email")
    return AccountContext(account_id=account_id, email=email if isinstance(email, str) else None)

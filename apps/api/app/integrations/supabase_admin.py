"""Supabase Auth admin API, server-side only (Plan 8 Task 2: account deletion).

Uses the server secret key, which never leaves the API. Logs and exceptions carry no key and
no response body.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Annotated, Protocol
from uuid import UUID

import httpx
from fastapi import Depends
from pydantic import SecretStr

from app.core.config import Settings, get_app_settings

logger = logging.getLogger(__name__)

ADMIN_TIMEOUT_S = 15.0


class AdminUnavailable(Exception):
    """Auth admin is not configured, unreachable, or refused the call."""


class SupabaseAdmin(Protocol):
    async def delete_user(self, user_id: UUID) -> None:
        """Delete the auth user. An already-deleted user (404) counts as success."""
        ...


class SupabaseAuthAdmin:
    def __init__(self, http: httpx.AsyncClient, *, url: str, secret_key: SecretStr) -> None:
        self._http = http
        self._base = f"{url.rstrip('/')}/auth/v1/admin"
        self._key = secret_key

    def __repr__(self) -> str:
        return "SupabaseAuthAdmin()"

    def _headers(self) -> dict[str, str]:
        key = self._key.get_secret_value()
        return {"Authorization": f"Bearer {key}", "apikey": key}

    async def delete_user(self, user_id: UUID) -> None:
        url = f"{self._base}/users/{user_id}"
        try:
            response = await self._http.delete(url, headers=self._headers())
        except httpx.HTTPError:
            logger.warning("auth_admin_delete status=network_error")
            raise AdminUnavailable("network error") from None
        if response.status_code in (200, 204, 404):
            return
        logger.warning("auth_admin_delete status=%d", response.status_code)
        raise AdminUnavailable(f"status {response.status_code}")


class _UnconfiguredAdmin:
    async def delete_user(self, user_id: UUID) -> None:
        raise AdminUnavailable("not configured")


async def get_supabase_admin(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AsyncIterator[SupabaseAdmin]:
    """FastAPI dependency: the Supabase Auth admin client for this request."""
    if not settings.supabase_url or settings.supabase_secret_key is None:
        yield _UnconfiguredAdmin()
        return
    async with httpx.AsyncClient(timeout=ADMIN_TIMEOUT_S) as http:
        yield SupabaseAuthAdmin(
            http, url=settings.supabase_url, secret_key=settings.supabase_secret_key
        )

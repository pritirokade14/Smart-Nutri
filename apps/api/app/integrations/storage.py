"""Supabase Storage (private label-photo and voice-answer buckets) over its REST API,
server-side only.

Uses the server secret key, which never leaves the API. Logs and exceptions carry no key,
no image bytes and no response body.

Note: Supabase fixes the lifetime of a signed *upload* token on the server
(`uploadSignedUrlExpirationTime`, 2 h by default); the REST call has no expiry parameter.
`expires_in` is what the API promises clients (600 s), not what Supabase enforces.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Annotated, Protocol
from urllib.parse import quote

import httpx
from fastapi import Depends
from pydantic import SecretStr

from app.core.config import Settings, get_app_settings

logger = logging.getLogger(__name__)

STORAGE_TIMEOUT_S = 20.0
# Read at most this much of an object; anything longer is already over the 8 MB limit.
DEFAULT_MAX_DOWNLOAD_BYTES = 8 * 1024 * 1024 + 1


class StorageNotFound(Exception):
    """The object does not exist (or is not visible to us)."""


class StorageUnavailable(Exception):
    """Storage is not configured, unreachable, or returned an unexpected error."""


class StorageClient(Protocol):
    async def create_signed_upload(self, path: str, expires_in: int) -> str:
        """Return an absolute URL the client PUTs the file to."""
        ...

    async def download(self, path: str) -> bytes:
        """Return the object's bytes. Raises StorageNotFound."""
        ...

    async def upload(self, path: str, data: bytes, content_type: str) -> None:
        """Store `data` at `path` (never overwriting). Raises StorageUnavailable."""
        ...

    async def create_signed_url(self, path: str, expires_in: int) -> str:
        """An absolute URL that GETs the object for `expires_in` seconds."""
        ...


def _is_not_found(response: httpx.Response) -> bool:
    if response.status_code == 404:
        return True
    if response.status_code != 400:
        return False
    # Supabase Storage historically answers a missing object with 400 + statusCode "404".
    try:
        body = response.json()
    except ValueError:
        return False
    if not isinstance(body, dict):
        return False
    error = str(body.get("error", "")).lower()
    return str(body.get("statusCode")) == "404" or error in {"not_found", "object not found"}


class SupabaseStorage:
    def __init__(
        self,
        http: httpx.AsyncClient,
        *,
        url: str,
        secret_key: SecretStr,
        bucket: str,
        max_download_bytes: int = DEFAULT_MAX_DOWNLOAD_BYTES,
    ) -> None:
        self._http = http
        self._base = f"{url.rstrip('/')}/storage/v1"
        self._key = secret_key
        self._bucket = bucket
        self._max = max_download_bytes

    def __repr__(self) -> str:
        return f"SupabaseStorage(bucket={self._bucket!r})"

    def _headers(self) -> dict[str, str]:
        key = self._key.get_secret_value()
        return {"Authorization": f"Bearer {key}", "apikey": key}

    def _object(self, path: str) -> str:
        return f"{quote(self._bucket, safe='')}/{quote(path, safe='/')}"

    async def create_signed_upload(self, path: str, expires_in: int) -> str:
        url = f"{self._base}/object/upload/sign/{self._object(path)}"
        try:
            response = await self._http.post(url, headers=self._headers(), json={})
        except httpx.HTTPError:
            logger.warning("storage_sign_upload status=network_error")
            raise StorageUnavailable("network error") from None
        if response.status_code != 200:
            logger.warning("storage_sign_upload status=%d", response.status_code)
            raise StorageUnavailable("sign upload failed")
        try:
            signed = response.json()["url"]
        except (ValueError, KeyError, TypeError):
            signed = None
        if not isinstance(signed, str) or not signed.startswith("/"):
            logger.warning("storage_sign_upload status=malformed")
            raise StorageUnavailable("malformed response")
        return f"{self._base}{signed}"

    async def download(self, path: str) -> bytes:
        url = f"{self._base}/object/authenticated/{self._object(path)}"
        try:
            async with self._http.stream("GET", url, headers=self._headers()) as response:
                if response.status_code != 200:
                    await response.aread()
                    if _is_not_found(response):
                        raise StorageNotFound(path)
                    logger.warning("storage_download status=%d", response.status_code)
                    raise StorageUnavailable("download failed")
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    chunks.append(chunk)
                    size += len(chunk)
                    if size > self._max:
                        break  # over the limit: the caller rejects it, no need for the rest
                return b"".join(chunks)[: self._max + 1]
        except httpx.HTTPError:
            logger.warning("storage_download status=network_error")
            raise StorageUnavailable("network error") from None

    async def upload(self, path: str, data: bytes, content_type: str) -> None:
        url = f"{self._base}/object/{self._object(path)}"
        headers = {**self._headers(), "Content-Type": content_type}
        try:
            response = await self._http.post(url, headers=headers, content=data)
        except httpx.HTTPError:
            logger.warning("storage_upload status=network_error")
            raise StorageUnavailable("network error") from None
        if response.status_code != 200:
            logger.warning("storage_upload status=%d", response.status_code)
            raise StorageUnavailable("upload failed")

    async def create_signed_url(self, path: str, expires_in: int) -> str:
        url = f"{self._base}/object/sign/{self._object(path)}"
        try:
            response = await self._http.post(
                url, headers=self._headers(), json={"expiresIn": expires_in}
            )
        except httpx.HTTPError:
            logger.warning("storage_sign_url status=network_error")
            raise StorageUnavailable("network error") from None
        if response.status_code != 200:
            logger.warning("storage_sign_url status=%d", response.status_code)
            raise StorageUnavailable("sign url failed")
        try:
            signed = response.json()["signedURL"]
        except (ValueError, KeyError, TypeError):
            signed = None
        if not isinstance(signed, str) or not signed.startswith("/"):
            logger.warning("storage_sign_url status=malformed")
            raise StorageUnavailable("malformed response")
        return f"{self._base}{signed}"


class _UnconfiguredStorage:
    async def create_signed_upload(self, path: str, expires_in: int) -> str:
        raise StorageUnavailable("not configured")

    async def download(self, path: str) -> bytes:
        raise StorageUnavailable("not configured")

    async def upload(self, path: str, data: bytes, content_type: str) -> None:
        raise StorageUnavailable("not configured")

    async def create_signed_url(self, path: str, expires_in: int) -> str:
        raise StorageUnavailable("not configured")


async def _storage(settings: Settings, bucket: str) -> AsyncIterator[StorageClient]:
    if not settings.supabase_url or settings.supabase_secret_key is None:
        yield _UnconfiguredStorage()
        return
    async with httpx.AsyncClient(timeout=STORAGE_TIMEOUT_S) as http:
        yield SupabaseStorage(
            http,
            url=settings.supabase_url,
            secret_key=settings.supabase_secret_key,
            bucket=bucket,
        )


async def get_storage(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AsyncIterator[StorageClient]:
    """FastAPI dependency: the label-photo bucket for this request (closed afterwards)."""
    async for storage in _storage(settings, settings.supabase_storage_bucket):
        yield storage


async def get_voice_storage(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AsyncIterator[StorageClient]:
    """FastAPI dependency: the private voice-answer bucket (objects deleted after 24 h by the
    M6 retention job)."""
    async for storage in _storage(settings, settings.supabase_voice_bucket):
        yield storage

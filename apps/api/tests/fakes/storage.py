"""FakeStorage: a StorageClient for tests. Never calls Supabase."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

import httpx
from pydantic import SecretStr

from app.integrations.storage import StorageNotFound, StorageUnavailable, SupabaseStorage


def missing_bucket_storage(bucket: str) -> SupabaseStorage:
    """The real SupabaseStorage over a MockTransport where `bucket` does not exist (C1).
    Answers like older Supabase Storage releases: 400 with statusCode "404"."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = {"statusCode": "404", "error": "Bucket not found", "message": "Bucket not found"}
        return httpx.Response(400, json=body)

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return SupabaseStorage(
        http, url="https://proj.supabase.co", secret_key=SecretStr("sb_secret_x"), bucket=bucket
    )


class FakeStorage:
    """Serves `objects[path]`, else `default` (bytes, or a callable of the path), else 404."""

    def __init__(
        self,
        objects: dict[str, bytes] | None = None,
        *,
        default: bytes | Callable[[str], bytes] | None = None,
        created: dict[str, datetime] | None = None,
    ) -> None:
        self.objects = dict(objects or {})
        self.default = default
        self.signed: list[tuple[str, int]] = []
        self.downloads: list[str] = []
        self.uploads: list[tuple[str, str]] = []  # (path, content_type)
        self.upserts: list[str] = []  # paths written with upsert=True
        self.signed_urls: list[tuple[str, int]] = []
        self.fail_uploads = False
        # Object creation times for list_prefix(older_than=...); missing means "just now".
        self.created = dict(created or {})
        self.deleted: list[str] = []
        self.unavailable = False  # True: list_prefix/delete_paths raise StorageUnavailable

    async def upload(
        self, path: str, data: bytes, content_type: str, *, upsert: bool = False
    ) -> None:
        if self.fail_uploads:
            raise StorageUnavailable("fake")
        if path in self.objects and not upsert:
            raise StorageUnavailable("fake: object exists")  # Supabase answers 400/409
        self.uploads.append((path, content_type))
        if upsert:
            self.upserts.append(path)
        self.objects[path] = data

    async def create_signed_url(self, path: str, expires_in: int) -> str:
        self.signed_urls.append((path, expires_in))
        return f"https://storage.test/sign/{path}?token=fake"

    async def create_signed_upload(self, path: str, expires_in: int) -> str:
        self.signed.append((path, expires_in))
        return f"https://storage.test/upload/{path}?token=fake"

    async def download(self, path: str) -> bytes:
        self.downloads.append(path)
        if path in self.objects:
            return self.objects[path]
        if callable(self.default):
            return self.default(path)
        if self.default is not None:
            return self.default
        raise StorageNotFound(path)

    async def list_prefix(self, prefix: str, *, older_than: datetime | None = None) -> list[str]:
        if self.unavailable:
            raise StorageUnavailable("fake outage")
        folder = prefix.strip("/")
        now = datetime.now(UTC)
        return sorted(
            path
            for path in self.objects
            if (not folder or path.startswith(folder + "/"))
            and (older_than is None or self.created.get(path, now) < older_than)
        )

    async def delete_paths(self, paths: Sequence[str]) -> None:
        if self.unavailable:
            raise StorageUnavailable("fake outage")
        for path in paths:
            if self.objects.pop(path, None) is not None:
                self.deleted.append(path)

"""FakeStorage: a StorageClient for tests. Never calls Supabase."""

from __future__ import annotations

from collections.abc import Callable

from app.integrations.storage import StorageNotFound


class FakeStorage:
    """Serves `objects[path]`, else `default` (bytes, or a callable of the path), else 404."""

    def __init__(
        self,
        objects: dict[str, bytes] | None = None,
        *,
        default: bytes | Callable[[str], bytes] | None = None,
    ) -> None:
        self.objects = dict(objects or {})
        self.default = default
        self.signed: list[tuple[str, int]] = []
        self.downloads: list[str] = []
        self.uploads: list[tuple[str, str]] = []  # (path, content_type)
        self.signed_urls: list[tuple[str, int]] = []
        self.fail_uploads = False

    async def upload(self, path: str, data: bytes, content_type: str) -> None:
        if self.fail_uploads:
            from app.integrations.storage import StorageUnavailable

            raise StorageUnavailable("fake")
        self.uploads.append((path, content_type))
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

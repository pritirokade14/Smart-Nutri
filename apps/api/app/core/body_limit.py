"""Request body size caps, enforced before routing (I2).

Without this, FastAPI reads and parses the whole body (spooling multipart uploads to disk)
before any dependency runs, so auth, consent, the voice switch and rate limits cannot stop a
huge upload. This ASGI middleware:

- rejects a declared `Content-Length` over the cap at once, without reading the body;
- counts the bytes of a streamed (chunked) body as the app reads it, and aborts the read as
  soon as it passes the cap.

Both answer 413 with the error envelope, code `payload_too_large`.

Caps: `/v1/voice/ask` takes up to 6 MB (5 MB of audio plus the multipart form), and
`POST /v1/products` up to 3 MB (a full label's ingredient list). Everything else, including `/v1/scans/*` (label photos go straight to storage, never through the API)
and the Supabase auth hook, takes up to 64 KB.
"""

from collections.abc import Sequence

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

KB = 1024
MB = 1024 * 1024
DEFAULT_MAX_BODY_BYTES = 64 * KB
VOICE_MAX_BODY_BYTES = 6 * MB
# POST /v1/products accepts a whole printed label: up to 400 ingredients of 1000 characters
# and two 4000-character statements (products/schemas.py), about 408k characters. 3 MB fits
# that even as \u-escaped Devanagari (6 bytes a character) with room for the other fields.
PRODUCT_CREATE_MAX_BODY_BYTES = 3 * MB

# (path, cap): an entry ending in "/" covers every path under it; otherwise the path must
# match exactly. The first match wins; anything unmatched gets DEFAULT_MAX_BODY_BYTES.
BODY_CAPS: tuple[tuple[str, int], ...] = (
    ("/v1/voice/ask", VOICE_MAX_BODY_BYTES),
    ("/v1/products", PRODUCT_CREATE_MAX_BODY_BYTES),
    ("/v1/scans/", 64 * KB),
    ("/v1/auth/hooks/", 64 * KB),
)


class PayloadTooLarge(StarletteHTTPException):
    """Raised from `receive` once a streamed body passes the cap. A Starlette HTTPException,
    so FastAPI's body parsing re-raises it unchanged (instead of turning it into a 400) and
    the error handlers answer 413 `payload_too_large`."""

    def __init__(self) -> None:
        super().__init__(status_code=413)


def cap_for(path: str, caps: Sequence[tuple[str, int]] = BODY_CAPS) -> int:
    for prefix, cap in caps:
        if path == prefix or (prefix.endswith("/") and path.startswith(prefix)):
            return cap
    return DEFAULT_MAX_BODY_BYTES


def _declared_length(scope: Scope) -> int | None:
    for name, value in scope.get("headers", ()):
        if name == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, *, caps: Sequence[tuple[str, int]] = BODY_CAPS) -> None:
        self.app = app
        self.caps = tuple(caps)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        cap = cap_for(scope.get("path", ""), self.caps)
        declared = _declared_length(scope)
        if declared is not None and declared > cap:
            await _reject(scope, receive, send)
            return

        received = 0
        started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > cap:
                    raise PayloadTooLarge()
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except PayloadTooLarge:
            # Normally the app's error handlers already answered 413; this covers code that
            # reads the body outside them.
            if started:
                raise
            await _reject(scope, receive, send)


async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
    from app.core.errors import _envelope  # local: errors imports nothing from here

    response = _envelope(413, "payload_too_large")  # literal: tests/unit/test_error_codes_i18n
    # Ask the client to close: the unread body would otherwise be parsed as the next request.
    response.headers["connection"] = "close"
    await response(scope, receive, send)

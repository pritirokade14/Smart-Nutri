"""I2: request bodies are capped before routing (413 `payload_too_large`).

A declared Content-Length over the cap is refused without reading the body; a streamed
(chunked) body is cut off as soon as it passes the cap. Neither reaches auth, the consent
gate, the database or any paid call.
"""

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI, Request

from app.core.body_limit import (
    BODY_CAPS,
    DEFAULT_MAX_BODY_BYTES,
    VOICE_MAX_BODY_BYTES,
    BodySizeLimitMiddleware,
    cap_for,
)
from app.core.errors import install_error_handlers

KB = 1024
MB = 1024 * 1024
TOO_LARGE = {
    "error": {
        "code": "payload_too_large",
        "message_key": "error.payload_too_large",
        "details": {},
    }
}


async def chunks(total: int, size: int = 16 * KB) -> AsyncIterator[bytes]:
    sent = 0
    while sent < total:
        n = min(size, total - sent)
        sent += n
        yield b"x" * n


def test_caps():
    assert cap_for("/v1/voice/ask") == VOICE_MAX_BODY_BYTES == 6 * MB
    assert cap_for("/v1/scans/label") == 64 * KB
    assert cap_for("/v1/scans/upload-url") == 64 * KB
    assert cap_for("/v1/auth/hooks/send-sms") == 64 * KB
    assert cap_for("/v1/members") == DEFAULT_MAX_BODY_BYTES == 64 * KB
    # Exact match only: nothing else under /v1/voice inherits the 6 MB cap.
    assert cap_for("/v1/voice/ask/extra") == 64 * KB
    assert cap_for("/v1/voice") == 64 * KB
    assert all(cap <= 6 * MB for _, cap in BODY_CAPS)


# --- the real app: refused before routing, so no auth, consent or DB is reached --------------


@pytest.mark.parametrize(
    "path",
    ["/v1/members", "/v1/scans/label", "/v1/auth/hooks/send-sms", "/v1/analyze", "/v1/nope"],
)
async def test_declared_length_over_64kb_is_refused(client, path):
    r = await client.post(
        path, content=b"x" * (64 * KB + 1), headers={"content-type": "application/json"}
    )
    assert r.status_code == 413
    assert r.json() == TOO_LARGE


async def test_voice_body_over_6mb_is_refused(client):
    r = await client.post(
        "/v1/voice/ask",
        files={"audio": ("q.m4a", b"x" * (6 * MB), "audio/mp4")},
        data={"member_id": "11111111-1111-1111-1111-111111111111", "language": "en"},
    )
    assert r.status_code == 413 and r.json() == TOO_LARGE


async def test_voice_body_under_6mb_passes_the_cap(client):
    # 1 MB of audio: over the default cap, under the voice cap. It reaches the app, which
    # refuses it for having no token.
    r = await client.post(
        "/v1/voice/ask",
        files={"audio": ("q.m4a", b"x" * MB, "audio/mp4")},
        data={"member_id": "11111111-1111-1111-1111-111111111111", "language": "en"},
    )
    assert r.status_code == 401


async def test_streamed_body_over_the_cap_is_cut_off(client):
    r = await client.post(
        "/v1/members",
        content=chunks(256 * KB),
        headers={"content-type": "application/json"},
    )
    assert "content-length" not in r.request.headers  # really chunked
    assert r.status_code == 413 and r.json() == TOO_LARGE


async def test_streamed_voice_body_over_6mb_is_cut_off(client):
    async def multipart() -> AsyncIterator[bytes]:
        yield (
            b'--b\r\nContent-Disposition: form-data; name="audio"; filename="q.m4a"\r\n'
            b"Content-Type: audio/mp4\r\n\r\n"
        )
        async for chunk in chunks(6 * MB + 1, size=256 * KB):
            yield chunk

    r = await client.post(
        "/v1/voice/ask",
        content=multipart(),
        headers={"content-type": "multipart/form-data; boundary=b"},
    )
    assert "content-length" not in r.request.headers
    assert r.status_code == 413 and r.json() == TOO_LARGE


async def test_413_carries_cors_and_security_headers(client):
    r = await client.post(
        "/v1/members",
        content=b"x" * (64 * KB + 1),
        headers={"origin": "http://localhost:3000", "content-type": "application/json"},
    )
    assert r.status_code == 413
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert r.headers["x-content-type-options"] == "nosniff"


async def test_small_bodies_and_gets_pass(client):
    assert (await client.get("/v1/nope")).status_code == 404
    r = await client.post("/v1/members", json={"name": "Asha"})
    assert r.status_code == 401  # reached the app


# --- the middleware alone, against a route that reads the whole body ------------------------


def echo_app() -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)

    @app.post("/echo")
    async def echo(request: Request) -> dict:
        return {"size": len(await request.body())}

    @app.post("/stream")
    async def stream(request: Request) -> dict:
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
        return {"size": size}

    app.add_middleware(BodySizeLimitMiddleware, caps=(("/echo", 100), ("/stream", 100)))
    return app


@pytest.fixture
async def echo() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=echo_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        yield c


async def test_exactly_the_cap_is_accepted(echo):
    r = await echo.post("/echo", content=b"x" * 100)
    assert r.status_code == 200 and r.json() == {"size": 100}


async def test_one_byte_over_is_refused(echo):
    r = await echo.post("/echo", content=b"x" * 101)
    assert r.status_code == 413 and r.json() == TOO_LARGE


@pytest.mark.parametrize("path", ["/echo", "/stream"])
async def test_streamed_body_counts_every_chunk(echo, path):
    async def body() -> AsyncIterator[bytes]:
        for _ in range(4):
            yield b"x" * 30  # 120 bytes in 30-byte chunks, no Content-Length

    r = await echo.post(path, content=body())
    assert r.status_code == 413 and r.json() == TOO_LARGE

    async def small() -> AsyncIterator[bytes]:
        for _ in range(3):
            yield b"x" * 30

    r = await echo.post(path, content=small())
    assert r.status_code == 200 and r.json() == {"size": 90}


async def test_understated_content_length_is_still_cut_off(echo):
    # A client that lies about its length is caught by the byte count.
    async def body() -> AsyncIterator[bytes]:
        yield b"x" * 60
        yield b"x" * 60

    r = await echo.post("/echo", content=body(), headers={"content-length": "10"})
    assert r.status_code == 413

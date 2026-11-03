"""Plan 4 Task 4: signed upload URL and POST /v1/scans/label (cache, limits, errors)."""

import base64
import io
import logging
import re
import uuid
from uuid import UUID

import httpx
import pytest
from fastapi import Request
from PIL import Image
from sqlalchemy import select

from app.core.errors import ApiError
from app.core.ratelimit import consume
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.scans import service as scan_service
from app.features.scans.models import Scan
from app.features.scans.schemas import NutrientsIn, NutritionExtraction
from app.integrations.callmissed import get_llm_provider
from app.integrations.providers import ExtractionFailed, ProviderUnavailable
from app.integrations.storage import get_storage
from app.prompts import load_extraction_prompt
from tests.fakes.llm import FakeLLM
from tests.fakes.storage import FakeStorage

A = UUID("11111111-1111-1111-1111-111111111111")
B = UUID("22222222-2222-2222-2222-222222222222")
_PATH_RE = re.compile(r"^(?P<acct>[0-9a-f-]{36})/(?P<id>[0-9a-f-]{36})\.(?P<ext>jpg|png|webp)$")


# --- image helpers --------------------------------------------------------------------


def make_image(fmt: str = "JPEG", size=(64, 48), color=(200, 30, 30), exif=None) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color)
    kwargs = {"exif": exif} if exif is not None else {}
    img.save(buf, format=fmt, **kwargs)
    return buf.getvalue()


def gps_exif() -> bytes:
    exif = Image.Exif()
    exif[0x010F] = "PhoneMaker"  # Make
    exif[0x8825] = {1: "N", 2: (18.0, 31.0, 12.0), 3: "E", 4: (73.0, 51.0, 24.0)}  # GPS
    return exif.tobytes()


def extraction(**over) -> NutritionExtraction:
    per_100g = NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | {"sugars_g": 12.0}))
    data = {
        "product_name": "Test Biscuit",
        "brand": "Acme",
        "basis_detected": "per_100g",
        "per_100g": per_100g,
        "per_serving": None,
        "per_100_unit": "g",
        "serving_size_g": None,
        "serving_size_unit": None,
        "ingredients": ["Wheat flour", "Sugar"],
        "allergen_statement": "Contains wheat",
        "may_contain_statement": None,
        "claims": [],
        "veg_mark": "veg",
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
        "upper_bound_fields": [],
    }
    return NutritionExtraction(**(data | over))


# --- fixtures -------------------------------------------------------------------------


@pytest.fixture
def scan_app(app, db_session):
    async def _account(request: Request) -> AccountContext:
        acct = request.headers.get("x-test-account")
        if not acct:
            raise ApiError("auth_required", 401)
        return AccountContext(UUID(acct), None)

    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[current_account] = _account
    return app


def _client(app, account_id: UUID | None) -> httpx.AsyncClient:
    headers = {"x-test-account": str(account_id)} if account_id else {}
    c = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://t", headers=headers
    )
    c.account_id = account_id
    return c


@pytest.fixture
async def auth_client(scan_app):
    async with _client(scan_app, A) as c:
        yield c


@pytest.fixture
async def other_client(scan_app):
    async with _client(scan_app, B) as c:
        yield c


@pytest.fixture
async def anon_client(scan_app):
    async with _client(scan_app, None) as c:
        yield c


def _use_storage(app, storage: FakeStorage) -> FakeStorage:
    app.dependency_overrides[get_storage] = lambda: storage
    return storage


def _use_llm(app, llm: FakeLLM) -> FakeLLM:
    app.dependency_overrides[get_llm_provider] = lambda: llm
    return llm


@pytest.fixture
def jpeg_bytes() -> bytes:
    return make_image()


@pytest.fixture
def fake_storage_jpeg(scan_app, jpeg_bytes):
    return _use_storage(scan_app, FakeStorage(default=jpeg_bytes))


@pytest.fixture
def fake_storage_9mb(scan_app):
    return _use_storage(scan_app, FakeStorage(default=b"\xff\xd8\xff" + b"\0" * (9 * 1024 * 1024)))


@pytest.fixture
def fake_storage_pdf(scan_app):
    return _use_storage(scan_app, FakeStorage(default=b"%PDF-1.7\n" + b"\0" * 100))


@pytest.fixture
def fake_storage_unique_jpegs(scan_app):
    counter = iter(range(10_000))

    def _unique(_path: str) -> bytes:
        i = next(counter)
        # PNG: lossless, so neighbouring colours never encode to identical bytes.
        return make_image("PNG", size=(16, 16), color=(i % 256, (i // 256) % 256, 7))

    return _use_storage(scan_app, FakeStorage(default=_unique))


@pytest.fixture
def fake_llm_ok(scan_app):
    return _use_llm(scan_app, FakeLLM(extraction()))


@pytest.fixture
def fake_llm_raises_failed(scan_app):
    return _use_llm(scan_app, FakeLLM(ExtractionFailed("invalid output")))


@pytest.fixture
def fake_llm_unavailable(scan_app):
    return _use_llm(scan_app, FakeLLM(ProviderUnavailable("insufficient_credits")))


@pytest.fixture
def tiny_scan_limit(scan_app):
    scan_app.state.settings.rate_limit_label_scans_per_day = 1


@pytest.fixture
def scan_limit_used(db_session):
    from sqlalchemy import text

    async def _used(client) -> int:
        value = await db_session.scalar(
            text(
                "select coalesce(sum(count), 0) from rate_limit_counters "
                "where key = :k and bucket = 'label_scans'"
            ),
            {"k": f"acct:{client.account_id}"},
        )
        return int(value)

    return _used


def new_path(client, ext: str = "jpg") -> str:
    return f"{client.account_id}/{uuid.uuid4()}.{ext}"


async def post_label(client, path: str | None = None, **extra) -> httpx.Response:
    return await client.post("/v1/scans/label", json={"path": path or new_path(client), **extra})


async def scans_for(db_session, account_id: UUID) -> list[Scan]:
    return list((await db_session.scalars(select(Scan).where(Scan.account_id == account_id))).all())


# --- upload URL -----------------------------------------------------------------------


async def test_upload_url_path_scoped_to_account(auth_client, fake_storage_jpeg):
    r = await auth_client.post("/v1/scans/upload-url", json={"ext": "png"})
    assert r.status_code == 200
    body = r.json()
    assert body["path"].startswith(str(auth_client.account_id) + "/")
    m = _PATH_RE.match(body["path"])
    assert m and m["acct"] == str(A) and m["ext"] == "png"
    assert UUID(m["id"]).version == 4
    assert body["expires_in"] == 600
    assert body["upload_url"] == f"https://storage.test/upload/{body['path']}?token=fake"
    assert fake_storage_jpeg.signed == [(body["path"], 600)]


async def test_upload_url_paths_are_unique(auth_client, fake_storage_jpeg):
    paths = {
        (await auth_client.post("/v1/scans/upload-url", json={"ext": "jpg"})).json()["path"]
        for _ in range(3)
    }
    assert len(paths) == 3


async def test_upload_url_rejects_other_ext(auth_client, fake_storage_jpeg):
    r = await auth_client.post("/v1/scans/upload-url", json={"ext": "pdf"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert fake_storage_jpeg.signed == []


async def test_upload_url_requires_auth(anon_client, fake_storage_jpeg):
    r = await anon_client.post("/v1/scans/upload-url", json={"ext": "jpg"})
    assert r.status_code == 401


# --- extraction -----------------------------------------------------------------------


async def test_extracts_and_stores_draft(
    auth_client, fake_storage_jpeg, fake_llm_ok, db_session, scan_app, jpeg_bytes
):
    path = new_path(auth_client)
    r = await post_label(auth_client, path)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cached"] is False and fake_llm_ok.calls == 1
    assert body["prompt_version"] == "extraction_v1"
    assert body["draft"]["name"] == "Test Biscuit"
    assert body["draft"]["per_100g"]["sugars_g"] == 12.0
    assert body["draft"]["per_100g"]["protein_g"] is None  # never invented

    kwargs = fake_llm_ok.last_kwargs
    assert kwargs["model"] == scan_app.state.settings.callmissed_extraction_model
    assert kwargs["prompt_version"] == "extraction_v1"
    assert kwargs["schema"] is NutritionExtraction
    assert kwargs["mime"] == "image/jpeg"
    assert kwargs["prompt"] == load_extraction_prompt()[0]

    [scan] = await scans_for(db_session, A)
    assert scan.id == UUID(body["scan_id"])
    assert scan.image_path == path
    import hashlib

    assert scan.image_sha256 == hashlib.sha256(jpeg_bytes).hexdigest()
    assert scan.product_id is None
    assert scan.analysis["prompt_version"] == "extraction_v1"
    assert scan.analysis["draft"] == body["draft"]
    assert scan.analysis["cached"] is False


async def test_paid_extraction_counts_toward_limit(
    auth_client, fake_storage_jpeg, fake_llm_ok, scan_limit_used
):
    assert (await post_label(auth_client)).status_code == 200
    assert await scan_limit_used(auth_client) == 1


async def test_same_image_is_cached_and_free(
    auth_client,
    other_client,
    fake_storage_jpeg,
    fake_llm_ok,
    tiny_scan_limit,
    scan_limit_used,
    db_session,
):
    first = await post_label(auth_client)
    r = await post_label(other_client)
    assert r.status_code == 200, r.text
    assert r.json()["cached"] is True and fake_llm_ok.calls == 1
    assert await scan_limit_used(other_client) == 0
    assert await scan_limit_used(auth_client) == 1
    # The other account gets its own scan with the same draft, never the first scan's id.
    assert r.json()["scan_id"] != first.json()["scan_id"]
    assert r.json()["draft"] == first.json()["draft"]
    [own] = await scans_for(db_session, B)
    assert own.id == UUID(r.json()["scan_id"])
    assert own.image_path.startswith(f"{B}/")
    assert own.analysis["cached"] is True
    assert own.product_id is None


async def test_same_account_repeat_is_cached(
    auth_client, fake_storage_jpeg, fake_llm_ok, tiny_scan_limit, scan_limit_used
):
    await post_label(auth_client)
    r = await post_label(auth_client)
    assert r.status_code == 200 and r.json()["cached"] is True
    assert fake_llm_ok.calls == 1 and await scan_limit_used(auth_client) == 1


async def test_cache_hit_works_without_provider_key(
    scan_app, auth_client, other_client, fake_storage_jpeg, fake_llm_ok
):
    await post_label(auth_client)
    # The real provider dependency, no CallMissed key: a cache hit never builds the client.
    del scan_app.dependency_overrides[get_llm_provider]
    r = await post_label(other_client)
    assert r.status_code == 200 and r.json()["cached"] is True


async def test_missing_provider_key_is_503_on_cache_miss(scan_app, auth_client, fake_storage_jpeg):
    assert scan_app.state.settings.callmissed_api_key is None
    r = await post_label(auth_client)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "extraction_unavailable"
    assert "draft" not in r.json()


async def test_image_downscaled_and_metadata_stripped(scan_app, auth_client, fake_llm_ok):
    big = make_image(size=(3200, 2400), exif=gps_exif())
    assert Image.open(io.BytesIO(big)).getexif()  # the upload carries EXIF/GPS
    _use_storage(scan_app, FakeStorage(default=big))
    assert (await post_label(auth_client)).status_code == 200
    sent = fake_llm_ok.last_kwargs["image"]
    img = Image.open(io.BytesIO(sent))
    assert max(img.size) == 1600 and img.size == (1600, 1200)
    assert img.format == "JPEG"
    assert not img.getexif()
    assert "exif" not in img.info


@pytest.mark.parametrize("fmt", ["PNG", "WEBP"])
async def test_png_and_webp_accepted(scan_app, auth_client, fake_llm_ok, fmt):
    _use_storage(scan_app, FakeStorage(default=make_image(fmt)))
    ext = {"PNG": "png", "WEBP": "webp"}[fmt]
    r = await post_label(auth_client, new_path(auth_client, ext))
    assert r.status_code == 200, r.text
    assert fake_llm_ok.last_kwargs["mime"] == "image/jpeg"  # re-encoded


async def test_barcode_stored_with_scan(auth_client, fake_storage_jpeg, fake_llm_ok, db_session):
    r = await post_label(auth_client, barcode="8901063201089")
    assert r.status_code == 200
    [scan] = await scans_for(db_session, A)
    assert scan.analysis["barcode"] == "8901063201089"


async def test_invalid_barcode_422(auth_client, fake_storage_jpeg, fake_llm_ok):
    r = await post_label(auth_client, barcode="12ab")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_barcode"
    assert fake_llm_ok.calls == 0


async def test_logs_prompt_version_and_model_without_image(
    auth_client, fake_storage_jpeg, fake_llm_ok, scan_app, jpeg_bytes, caplog
):
    caplog.set_level(logging.INFO, logger="app.features.scans.service")
    await post_label(auth_client)
    text = caplog.text
    assert "prompt_version=extraction_v1" in text
    assert f"model={scan_app.state.settings.callmissed_extraction_model}" in text
    assert base64.b64encode(jpeg_bytes).decode()[:40] not in text
    assert "Test Biscuit" not in text


# --- rejected images ------------------------------------------------------------------


async def test_too_large(auth_client, fake_storage_9mb, fake_llm_ok, scan_limit_used):
    r = await post_label(auth_client)
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "image_too_large"
    assert fake_llm_ok.calls == 0 and await scan_limit_used(auth_client) == 0


async def test_not_an_image(auth_client, fake_storage_pdf, fake_llm_ok):
    r = await post_label(auth_client)
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "unsupported_image"
    assert fake_llm_ok.calls == 0


async def test_corrupt_image_with_jpeg_magic(scan_app, auth_client, fake_llm_ok, scan_limit_used):
    _use_storage(scan_app, FakeStorage(default=b"\xff\xd8\xff\xe0" + b"garbage" * 50))
    r = await post_label(auth_client)
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "unsupported_image"
    assert fake_llm_ok.calls == 0 and await scan_limit_used(auth_client) == 0


async def test_foreign_path_404(auth_client, fake_storage_jpeg, fake_llm_ok):
    r = await post_label(auth_client, path="someone-else/x.jpg")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "scan_image_not_found"
    assert fake_storage_jpeg.downloads == []


@pytest.mark.parametrize(
    "path",
    [
        f"{B}/{uuid.uuid4()}.jpg",  # another account's photo
        f"{A}/../{B}/{uuid.uuid4()}.jpg",  # traversal out of the caller's folder
        f"{A}/{uuid.uuid4()}.gif",
        f"{A}/nested/{uuid.uuid4()}.jpg",
        f"{A}",
    ],
)
async def test_paths_outside_own_folder_404(auth_client, fake_storage_jpeg, fake_llm_ok, path):
    r = await post_label(auth_client, path=path)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "scan_image_not_found"
    assert fake_storage_jpeg.downloads == []


async def test_missing_object_404(scan_app, auth_client, fake_llm_ok):
    _use_storage(scan_app, FakeStorage())
    r = await post_label(auth_client)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "scan_image_not_found"


async def test_label_requires_auth(anon_client, fake_storage_jpeg, fake_llm_ok):
    r = await post_label(anon_client, path=f"{A}/{uuid.uuid4()}.jpg")
    assert r.status_code == 401


# --- limits ---------------------------------------------------------------------------


async def test_rate_limited_after_30(auth_client, fake_storage_unique_jpegs, fake_llm_ok):
    for _ in range(30):
        assert (await post_label(auth_client)).status_code == 200
    r = await post_label(auth_client)
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "rate_limited_scans"
    assert r.json()["error"]["details"]["retry_after"] > 0
    assert int(r.headers["retry-after"]) >= 1
    assert fake_llm_ok.calls == 30


async def test_cache_hit_allowed_when_over_limit(
    auth_client, fake_storage_jpeg, fake_llm_ok, tiny_scan_limit
):
    await post_label(auth_client)  # A: paid (1/1)
    # A is now at its limit, but the same photo again is free and still served.
    r = await post_label(auth_client)
    assert r.status_code == 200 and r.json()["cached"] is True


async def test_consume_refuses_to_commit_staged_writes(db_session, scan_app):
    db_session.add(Scan(account_id=A, analysis={}))
    with pytest.raises(RuntimeError):
        await consume(db_session, scan_app.state.settings, account_id=A, bucket="label_scans")


# --- provider errors ------------------------------------------------------------------


async def test_provider_failure_returns_error_without_draft(
    auth_client, fake_storage_jpeg, fake_llm_raises_failed, db_session, scan_limit_used
):
    r = await post_label(auth_client)
    assert r.status_code == 502 and "draft" not in r.json()
    assert r.json()["error"]["code"] == "extraction_failed"
    assert await scans_for(db_session, A) == []  # no draft is ever stored
    assert await scan_limit_used(auth_client) == 1  # the paid attempt still counts


async def test_out_of_credits_is_503(
    auth_client, fake_storage_jpeg, fake_llm_unavailable, monkeypatch, db_session
):
    captured: list[tuple] = []
    monkeypatch.setattr(
        scan_service.sentry_sdk,
        "capture_message",
        lambda *a, **k: captured.append((a, k)),
    )
    r = await post_label(auth_client)
    assert r.status_code == 503 and "draft" not in r.json()
    assert r.json()["error"]["code"] == "extraction_unavailable"
    assert len(captured) == 1
    assert "insufficient_credits" in str(captured[0])
    assert await scans_for(db_session, A) == []


@pytest.mark.parametrize("reason", ["not_configured", "misconfigured"])
async def test_provider_not_configured_is_503(scan_app, auth_client, fake_storage_jpeg, reason):
    _use_llm(scan_app, FakeLLM(ProviderUnavailable(reason)))
    r = await post_label(auth_client)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "extraction_unavailable"

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
    # These tests drive the v1 schema (`extraction()`); the v2 tests at the end switch it.
    app.state.settings.extraction_prompt_version = "extraction_v1"
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


def assert_no_metadata(data: bytes) -> None:
    img = Image.open(io.BytesIO(data))
    assert img.format == "JPEG"
    assert not img.getexif()
    assert "exif" not in img.info and "xmp" not in img.info
    assert b"PhoneMaker" not in data  # the EXIF Make tag is nowhere in the bytes


# --- D1/S4: the stored photo itself carries no EXIF/GPS ---------------------------------


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
async def test_stored_photo_is_overwritten_without_exif(scan_app, auth_client, fake_llm_ok, fmt):
    ext = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[fmt]
    path = new_path(auth_client, ext)
    original = make_image(fmt, size=(3200, 2400), exif=gps_exif())
    assert Image.open(io.BytesIO(original)).getexif()  # the upload carries EXIF/GPS
    storage = _use_storage(scan_app, FakeStorage({path: original}))
    r = await post_label(auth_client, path)
    assert r.status_code == 200, r.text
    stored = storage.objects[path]
    assert stored != original
    assert_no_metadata(stored)
    # The same re-encode the model got (EXIF orientation applied, long edge 1600 px).
    assert stored == fake_llm_ok.last_kwargs["image"]
    assert storage.uploads == [(path, "image/jpeg")] and storage.upserts == [path]


async def test_stored_photo_is_stripped_on_a_cache_hit(
    scan_app, auth_client, other_client, fake_llm_ok
):
    original = make_image(exif=gps_exif())
    storage = _use_storage(scan_app, FakeStorage(default=original))
    first, second = new_path(auth_client), new_path(other_client)
    assert (await post_label(auth_client, first)).status_code == 200
    r = await post_label(other_client, second)
    assert r.status_code == 200 and r.json()["cached"] is True and fake_llm_ok.calls == 1
    assert_no_metadata(storage.objects[first])
    assert_no_metadata(storage.objects[second])


async def test_stored_photo_strip_failure_does_not_fail_the_scan(
    scan_app, auth_client, fake_llm_ok, caplog
):
    path = new_path(auth_client)
    storage = _use_storage(scan_app, FakeStorage({path: make_image(exif=gps_exif())}))
    storage.fail_uploads = True
    caplog.set_level(logging.WARNING, logger="app.features.scans.service")
    r = await post_label(auth_client, path)
    assert r.status_code == 200
    assert "label_photo_strip status=unavailable" in caplog.text
    assert path not in caplog.text


async def test_rejected_upload_is_deleted(scan_app, auth_client, fake_llm_ok):
    path = new_path(auth_client)
    storage = _use_storage(scan_app, FakeStorage({path: b"%PDF-1.7\n" + b"\0" * 100}))
    r = await post_label(auth_client, path)
    assert r.status_code == 415
    assert path not in storage.objects and storage.deleted == [path]


async def test_undecodable_upload_is_deleted(scan_app, auth_client, fake_llm_ok):
    path = new_path(auth_client)
    storage = _use_storage(scan_app, FakeStorage({path: b"\xff\xd8\xff\xe0" + b"junk" * 50}))
    assert (await post_label(auth_client, path)).status_code == 415
    assert path not in storage.objects


async def test_too_large_upload_is_deleted(scan_app, auth_client, fake_llm_ok):
    path = new_path(auth_client)
    big = b"\xff\xd8\xff" + b"\0" * (9 * 1024 * 1024)
    storage = _use_storage(scan_app, FakeStorage({path: big}))
    assert (await post_label(auth_client, path)).status_code == 413
    assert path not in storage.objects


async def test_rejected_upload_delete_failure_keeps_the_error(scan_app, auth_client, fake_llm_ok):
    path = new_path(auth_client)
    storage = _use_storage(scan_app, FakeStorage({path: b"%PDF-1.7\n"}))
    storage.unavailable = True
    r = await post_label(auth_client, path)
    assert r.status_code == 415 and r.json()["error"]["code"] == "unsupported_image"


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
    # R15: an undecodable upload still costs one label scan (counted before decode).
    assert fake_llm_ok.calls == 0 and await scan_limit_used(auth_client) == 1


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


async def _bucket_used(db_session, client, bucket: str) -> int:
    from sqlalchemy import text

    return int(
        await db_session.scalar(
            text(
                "select coalesce(sum(count), 0) from rate_limit_counters "
                "where key = :k and bucket = :b"
            ),
            {"k": f"acct:{client.account_id}", "b": bucket},
        )
    )


async def test_cache_hit_not_counted_as_label_scan(
    auth_client, fake_storage_jpeg, fake_llm_ok, scan_limit_used
):
    await post_label(auth_client)
    await post_label(auth_client)
    assert await scan_limit_used(auth_client) == 1


async def test_upload_url_rate_limited(scan_app, auth_client, fake_storage_jpeg):
    scan_app.state.settings.rate_limit_scan_uploads_per_day = 2
    codes = [
        (await auth_client.post("/v1/scans/upload-url", json={"ext": "jpg"})).status_code
        for _ in range(3)
    ]
    assert codes == [200, 200, 429]
    r = await auth_client.post("/v1/scans/upload-url", json={"ext": "jpg"})
    assert r.json()["error"]["code"] == "rate_limited"
    assert len(fake_storage_jpeg.signed) == 2


async def test_upload_url_default_limit_is_60(scan_app):
    assert scan_app.state.settings.rate_limit_scan_uploads_per_day == 60
    assert scan_app.state.settings.rate_limit_product_creates_per_day == 50
    assert scan_app.state.settings.rate_limit_label_requests_per_day == 200


async def test_label_requests_limit_blocks_before_download(
    scan_app, auth_client, fake_storage_jpeg, fake_llm_ok
):
    scan_app.state.settings.rate_limit_label_requests_per_day = 2
    assert (await post_label(auth_client)).status_code == 200
    assert (await post_label(auth_client)).status_code == 200  # cache hit still counts
    downloads = len(fake_storage_jpeg.downloads)
    calls = fake_llm_ok.calls
    r = await post_label(auth_client)
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
    assert len(fake_storage_jpeg.downloads) == downloads
    assert fake_llm_ok.calls == calls


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
    # The message is redacted by scrub_event (D1/S3); the tag keeps the alert identifiable.
    assert captured[0][1]["tags"] == {"alert": "callmissed_insufficient_credits"}
    assert await scans_for(db_session, A) == []


@pytest.mark.parametrize("reason", ["not_configured", "misconfigured"])
async def test_provider_not_configured_is_503(scan_app, auth_client, fake_storage_jpeg, reason):
    _use_llm(scan_app, FakeLLM(ProviderUnavailable(reason)))
    r = await post_label(auth_client)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "extraction_unavailable"


# --- Ruling R16 -------------------------------------------------------------------------------


def _sha(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


async def _seed_scan(db_session, account_id: UUID, sha: str, analysis: dict) -> Scan:
    from app.features.me.service import ensure_account

    await ensure_account(db_session, AccountContext(account_id, None))
    scan = Scan(
        account_id=account_id,
        image_path=f"{account_id}/{uuid.uuid4()}.jpg",
        image_sha256=sha,
        analysis=analysis,
    )
    db_session.add(scan)
    await db_session.flush()
    return scan


def _stale_draft() -> dict:
    from app.features.scans.normalize import to_draft

    stale = to_draft(extraction())
    return stale.model_dump(mode="json") | {
        "per_100g": stale.per_100g.model_dump() | {"sugars_g": 99.0}
    }


# (1) the cache stores the raw extraction and re-normalises it on every hit


async def test_extraction_and_model_are_stored(
    auth_client, fake_storage_jpeg, fake_llm_ok, db_session, scan_app
):
    r = await post_label(auth_client)
    assert r.status_code == 200, r.text
    [scan] = await scans_for(db_session, A)
    assert scan.analysis["extraction"] == extraction().model_dump(mode="json")
    assert scan.analysis["model"] == scan_app.state.settings.callmissed_extraction_model


async def test_old_style_cache_row_without_extraction_is_a_miss(
    scan_app, auth_client, fake_storage_jpeg, fake_llm_ok, db_session, jpeg_bytes
):
    await _seed_scan(
        db_session,
        B,
        _sha(jpeg_bytes),
        {
            "draft": _stale_draft(),
            "prompt_version": "extraction_v1",
            "model": scan_app.state.settings.callmissed_extraction_model,
        },
    )
    r = await post_label(auth_client)
    assert r.status_code == 200, r.text
    assert r.json()["cached"] is False and fake_llm_ok.calls == 1
    assert r.json()["draft"]["per_100g"]["sugars_g"] == 12.0


async def test_cache_hit_re_runs_the_normaliser(
    scan_app, auth_client, fake_storage_jpeg, fake_llm_ok, db_session, jpeg_bytes, monkeypatch
):
    # A row from an older normaliser: raw extraction plus a stale draft.
    await _seed_scan(
        db_session,
        B,
        _sha(jpeg_bytes),
        {
            "draft": _stale_draft(),
            "extraction": extraction().model_dump(mode="json"),
            "prompt_version": "extraction_v1",
            "model": scan_app.state.settings.callmissed_extraction_model,
        },
    )
    seen: list = []
    real = scan_service.to_draft

    def spy(e):
        seen.append(e)
        return real(e)

    monkeypatch.setattr(scan_service, "to_draft", spy)
    r = await post_label(auth_client)
    assert r.status_code == 200, r.text
    assert r.json()["cached"] is True and fake_llm_ok.calls == 0
    assert seen == [extraction()]
    assert r.json()["draft"]["per_100g"]["sugars_g"] == 12.0  # fresh, not the stale 99
    [own] = await scans_for(db_session, A)
    assert own.analysis["draft"] == r.json()["draft"]
    assert own.analysis["extraction"] == extraction().model_dump(mode="json")


async def test_cache_key_includes_the_model(
    scan_app, auth_client, other_client, fake_storage_jpeg, fake_llm_ok, db_session
):
    scan_app.state.settings.callmissed_extraction_model = "vision-a"
    assert (await post_label(auth_client)).json()["cached"] is False
    scan_app.state.settings.callmissed_extraction_model = "vision-b"
    r = await post_label(other_client)
    assert r.json()["cached"] is False and fake_llm_ok.calls == 2
    # (7) the stored model is the one that produced the draft
    [a] = await scans_for(db_session, A)
    [b] = await scans_for(db_session, B)
    assert a.analysis["model"] == "vision-a" and b.analysis["model"] == "vision-b"


async def test_cache_hit_stores_the_model_of_the_cached_extraction(
    scan_app, auth_client, other_client, fake_storage_jpeg, fake_llm_ok, db_session
):
    scan_app.state.settings.callmissed_extraction_model = "vision-a"
    await post_label(auth_client)
    r = await post_label(other_client)
    assert r.json()["cached"] is True
    [b] = await scans_for(db_session, B)
    assert b.analysis["model"] == "vision-a"


# (2) the same account posting the same path twice gets the same scan


async def test_same_path_twice_returns_the_same_scan(
    auth_client, fake_storage_jpeg, fake_llm_ok, db_session, scan_limit_used
):
    path = new_path(auth_client)
    first = await post_label(auth_client, path)
    second = await post_label(auth_client, path)
    assert first.status_code == second.status_code == 200
    assert second.json()["scan_id"] == first.json()["scan_id"]
    assert second.json()["draft"] == first.json()["draft"]
    assert len(await scans_for(db_session, A)) == 1
    assert fake_llm_ok.calls == 1 and await scan_limit_used(auth_client) == 1


async def test_same_path_with_new_bytes_returns_the_existing_scan(
    auth_client, fake_storage_unique_jpegs, fake_llm_ok, db_session, scan_limit_used
):
    # R21(d): one scan per (account, path). Signed uploads never overwrite an object, so
    # new bytes at a used path are not a new photo; nothing is paid for twice.
    path = new_path(auth_client, "png")
    first = await post_label(auth_client, path)
    second = await post_label(auth_client, path)
    assert first.status_code == second.status_code == 200
    assert second.json()["scan_id"] == first.json()["scan_id"]
    assert second.json()["cached"] is True
    assert len(await scans_for(db_session, A)) == 1
    assert fake_llm_ok.calls == 1 and await scan_limit_used(auth_client) == 1


async def test_same_path_after_a_model_change_returns_the_existing_scan(
    scan_app, auth_client, fake_storage_jpeg, fake_llm_ok, db_session
):
    path = new_path(auth_client)
    scan_app.state.settings.callmissed_extraction_model = "vision-a"
    first = await post_label(auth_client, path)
    scan_app.state.settings.callmissed_extraction_model = "vision-b"
    second = await post_label(auth_client, path)
    assert second.json()["scan_id"] == first.json()["scan_id"]
    assert fake_llm_ok.calls == 1 and len(await scans_for(db_session, A)) == 1


async def test_same_path_is_answered_without_downloading_again(
    auth_client, fake_storage_jpeg, fake_llm_ok
):
    path = new_path(auth_client)
    await post_label(auth_client, path)
    downloads = len(fake_storage_jpeg.downloads)
    await post_label(auth_client, path)
    assert len(fake_storage_jpeg.downloads) == downloads


class _RacingLLM(FakeLLM):
    """A concurrent request for the same path stores its scan while this one is extracting."""

    def __init__(self, db_session, path: str) -> None:
        super().__init__(extraction())
        self._db, self._path = db_session, path
        self.racer: Scan | None = None

    async def extract_label(self, **kwargs: object):
        result = await super().extract_label(**kwargs)
        from app.features.scans.normalize import to_draft
        from app.features.scans.service import label_scan_analysis

        self.racer = Scan(
            account_id=A,
            image_path=self._path,
            image_sha256="racer",
            analysis=label_scan_analysis(
                to_draft(extraction(product_name="Racer")),
                extraction=extraction(product_name="Racer"),
                prompt_version="extraction_v1",
                model="vision-racer",
            ),
        )
        self._db.add(self.racer)
        await self._db.flush()
        return result


async def test_concurrent_first_posts_of_a_path_make_one_scan(
    scan_app, auth_client, fake_storage_jpeg, db_session
):
    path = new_path(auth_client)
    llm = _use_llm(scan_app, _RacingLLM(db_session, path))
    r = await post_label(auth_client, path)
    assert r.status_code == 200, r.text
    # The insert hit the unique index: the scan that won the race is returned, no second row.
    assert r.json()["scan_id"] == str(llm.racer.id)
    assert r.json()["draft"]["name"] == "Racer"
    rows = await scans_for(db_session, A)
    assert [s.id for s in rows if s.image_path == path] == [llm.racer.id]


# (3) the DB connection is released before the storage download


async def test_no_open_transaction_during_download(scan_app, auth_client, fake_llm_ok, db_session):
    seen: list[bool] = []
    image = make_image()

    def _download(_path: str) -> bytes:
        seen.append(db_session.in_transaction())
        return image

    _use_storage(scan_app, FakeStorage(default=_download))
    assert (await post_label(auth_client)).status_code == 200
    assert seen == [False]


# (6) a refused provider call is refunded; a failed paid call is not


async def test_provider_unavailable_refunds_the_scan(
    auth_client, fake_storage_jpeg, fake_llm_unavailable, scan_limit_used, monkeypatch
):
    monkeypatch.setattr(scan_service.sentry_sdk, "capture_message", lambda *a, **k: None)
    r = await post_label(auth_client)
    assert r.status_code == 503
    assert await scan_limit_used(auth_client) == 0


async def test_missing_provider_key_refunds_the_scan(
    scan_app, auth_client, fake_storage_jpeg, scan_limit_used
):
    r = await post_label(auth_client)
    assert r.status_code == 503 and r.json()["error"]["code"] == "extraction_unavailable"
    assert await scan_limit_used(auth_client) == 0


async def test_refund_is_floored_at_zero(db_session, scan_app, scan_limit_used):
    from app.core.ratelimit import refund

    settings = scan_app.state.settings
    client = type("C", (), {"account_id": A})()
    await refund(db_session, settings, account_id=A, bucket="label_scans")  # no counter yet
    assert await scan_limit_used(client) == 0
    await consume(db_session, settings, account_id=A, bucket="label_scans")
    await refund(db_session, settings, account_id=A, bucket="label_scans")
    await refund(db_session, settings, account_id=A, bucket="label_scans")
    assert await scan_limit_used(client) == 0


async def test_refund_refuses_to_commit_staged_writes(db_session, scan_app):
    from app.core.ratelimit import refund

    db_session.add(Scan(account_id=A, analysis={}))
    with pytest.raises(RuntimeError):
        await refund(db_session, scan_app.state.settings, account_id=A, bucket="label_scans")


async def test_refund_rejects_unknown_buckets(db_session, scan_app):
    from app.core.ratelimit import refund

    for bucket in ("public", "nope"):
        with pytest.raises(KeyError):
            await refund(db_session, scan_app.state.settings, account_id=A, bucket=bucket)


# (8) the upload URL route creates the account row


async def test_upload_url_creates_the_account_row(auth_client, fake_storage_jpeg, db_session):
    from app.features.me.models import Account

    assert await db_session.get(Account, A) is None
    r = await auth_client.post("/v1/scans/upload-url", json={"ext": "jpg"})
    assert r.status_code == 200
    assert await db_session.get(Account, A, populate_existing=True) is not None


# --- label accuracy v2: extraction_v2 (raw cells parsed in code) ------------------------


def extraction_v2(**over):
    from app.features.scans.schemas import CellIn, NutrientCellsIn, NutritionExtractionV2

    cells = dict.fromkeys(NutrientCellsIn.model_fields) | {
        "sugars_g": CellIn(printed="१२", unit_label="ग्रा"),
        "protein_g": CellIn(printed="<0.5 g", unit_label=None),
    }
    data = {
        "product_name": "Test Biscuit",
        "brand": "Acme",
        "basis_detected": "per_100g",
        "per_100g": NutrientCellsIn(**cells),
        "per_serving": None,
        "per_100_unit": "g",
        "serving_size": None,
        "ingredients": ["Wheat flour", "Sugar"],
        "allergen_statement": "Contains wheat",
        "may_contain_statement": None,
        "claims": [],
        "veg_mark": "veg",
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
    }
    return NutritionExtractionV2(**(data | over))


@pytest.fixture
def v2(scan_app):
    scan_app.state.settings.extraction_prompt_version = "extraction_v2"
    return scan_app


def test_v2_is_the_default_prompt():
    from app.core.config import Settings

    assert Settings(_env_file=None).extraction_prompt_version == "extraction_v2"


async def test_v2_extraction_is_parsed_in_code(v2, auth_client, fake_storage_jpeg, db_session):
    from app.features.scans.schemas import NutritionExtractionV2

    llm = _use_llm(v2, FakeLLM(extraction_v2()))
    r = await post_label(auth_client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["prompt_version"] == "extraction_v2"
    assert body["draft"]["per_100g"]["sugars_g"] == 12.0  # Devanagari digits
    assert body["draft"]["per_100g"]["protein_g"] == 0.5
    assert "upper_bound:per_100g.protein_g" in body["draft"]["warnings"]
    assert body["draft"]["engine_withheld"] == ["protein_g"]

    kwargs = llm.last_kwargs
    assert kwargs["schema"] is NutritionExtractionV2
    assert kwargs["prompt_version"] == "extraction_v2"
    assert kwargs["prompt"] == load_extraction_prompt("extraction_v2")[0]

    [scan] = await scans_for(db_session, A)
    assert scan.analysis["prompt_version"] == "extraction_v2"
    # The raw cells are stored (the cache entry); every reuse parses them again.
    assert scan.analysis["extraction"] == extraction_v2().model_dump(mode="json")
    stored = await scan_service.get_label_scan(db_session, A, scan.id)
    assert stored is not None and stored.draft.model_dump(mode="json") == body["draft"]


async def test_v2_cache_hit_is_free_and_re_parsed(v2, auth_client, other_client, fake_storage_jpeg):
    llm = _use_llm(v2, FakeLLM(extraction_v2()))
    first = await post_label(auth_client)
    second = await post_label(other_client)
    assert second.status_code == 200, second.text
    assert second.json()["cached"] is True and llm.calls == 1
    assert second.json()["draft"] == first.json()["draft"]


async def test_v2_same_path_again_returns_the_stored_scan(v2, auth_client, fake_storage_jpeg):
    llm = _use_llm(v2, FakeLLM(extraction_v2()))
    path = new_path(auth_client)
    first = await post_label(auth_client, path)
    again = await post_label(auth_client, path)
    assert again.status_code == 200, again.text
    assert again.json()["scan_id"] == first.json()["scan_id"] and llm.calls == 1
    assert again.json()["draft"] == first.json()["draft"]
    assert again.json()["prompt_version"] == "extraction_v2"


async def test_switching_prompt_version_is_a_cache_miss(
    v2, auth_client, other_client, fake_storage_jpeg
):
    _use_llm(v2, FakeLLM(extraction_v2()))
    assert (await post_label(auth_client)).status_code == 200
    v2.state.settings.extraction_prompt_version = "extraction_v1"
    llm_v1 = _use_llm(v2, FakeLLM(extraction()))
    r = await post_label(other_client)
    assert r.status_code == 200, r.text
    assert r.json()["cached"] is False and llm_v1.calls == 1
    assert r.json()["prompt_version"] == "extraction_v1"
    assert llm_v1.last_kwargs["schema"] is NutritionExtraction


async def test_v2_wrong_schema_from_the_provider_is_extraction_failed(
    v2, auth_client, fake_storage_jpeg
):
    _use_llm(v2, FakeLLM(extraction()))  # a v1 object for a v2 request
    r = await post_label(auth_client)
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "extraction_failed"

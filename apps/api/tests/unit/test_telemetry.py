"""Plan 8 Task 4: no health data in telemetry (Sentry scrubbing, PostHog allow-list)."""

import hashlib
import json
import logging
from unittest.mock import MagicMock
from uuid import UUID

import httpx
import pytest
import sentry_sdk
from fastapi import Body
from sentry_sdk.transport import Transport

from app.core import observability
from app.core.config import Settings
from app.core.observability import scrub_event
from app.integrations import posthog
from app.integrations.posthog import ALLOWED_EVENTS, track
from app.main import create_app

ACC = UUID("11111111-1111-1111-1111-111111111111")
HASHED = hashlib.sha256(str(ACC).encode()).hexdigest()
HEALTH = ("diabetes", "peanut", "allergen_contains", "Asha", "asha@example.com")


# --- Sentry ------------------------------------------------------------------------------


def _event() -> dict:
    return {
        "request": {
            "url": "https://api.test/v1/members?token=abc&code=123",
            "method": "POST",
            "data": {"name": "Asha", "allergens": ["peanut"], "conditions": ["diabetes"]},
            "cookies": {"sb-access-token": "x"},
            "query_string": "token=abc&code=123",
            "headers": {
                "Authorization": "Bearer t",
                "Cookie": "sb=1",
                "apikey": "k",
                "User-Agent": "ua",
            },
            "env": {"REMOTE_ADDR": "1.2.3.4"},
        },
        "user": {"id": str(ACC), "email": "asha@example.com", "ip_address": "1.2.3.4"},
    }


def test_scrub_removes_auth_header_cookies_body():
    out = scrub_event(_event(), {})
    request = out["request"]
    assert "data" not in request and "cookies" not in request
    assert "query_string" not in request and "env" not in request
    assert request["url"] == "https://api.test/v1/members"
    assert set(request["headers"]) == {"User-Agent"}
    assert not any(word in json.dumps(out) for word in HEALTH)


def test_scrub_hashes_user_id():
    out = scrub_event(_event(), {})
    assert out["user"] == {"id": HASHED}


def test_scrub_hash_is_stable_and_not_double_hashed():
    once = scrub_event({"user": {"id": str(ACC)}}, {})
    assert once["user"]["id"] == HASHED
    # A hashed id (already 64 hex chars) is left alone if the hook ever runs twice.
    assert scrub_event(once, {})["user"]["id"] == HASHED


def test_scrub_cleans_transaction_spans():
    event = {
        "type": "transaction",
        "spans": [
            {
                "op": "http.client",
                "description": "GET https://off.test/api?barcode=1&token=x",
                "data": {"http.query": "token=x", "url": "https://off.test/api"},
            },
            {"op": "db", "description": "select 1", "data": {"db.params": ["diabetes"]}},
        ],
    }
    out = scrub_event(event, {})
    assert out["spans"][0]["description"] == "GET https://off.test/api"
    assert "http.query" not in out["spans"][0]["data"]
    assert "db.params" not in out["spans"][1]["data"]
    assert "diabetes" not in json.dumps(out)


class _Capture(Transport):
    def __init__(self, options=None):
        super().__init__(options)
        self.events: list[dict] = []

    def capture_envelope(self, envelope):
        for item in envelope.items:
            payload = item.payload.json
            if payload is not None:
                self.events.append(payload)


@pytest.fixture
def sentry_capture(monkeypatch):
    transport = _Capture()
    real_init = sentry_sdk.init
    monkeypatch.setattr(
        observability.sentry_sdk, "init", lambda **kw: real_init(transport=transport, **kw)
    )
    yield transport
    sentry_sdk.get_client().close()
    real_init()  # back to a disabled client for the rest of the session


async def test_end_to_end_error_event_carries_no_health_data(sentry_capture):
    app = create_app(
        Settings(
            _env_file=None,
            environment="test",
            sentry_dsn="https://public@o0.ingest.sentry.io/1",
        )
    )

    @app.post("/boom")
    async def boom(body: dict = Body(...)) -> None:  # noqa: B008 - test route
        conditions = body["conditions"]  # noqa: F841 - a local Sentry must not capture
        raise RuntimeError(f"failed for {body['name']} with {body['allergens']}")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://t"
    ) as client:
        r = await client.post(
            "/boom?token=abc",
            json={"name": "Asha", "allergens": ["peanut"], "conditions": ["diabetes"]},
            headers={"Authorization": "Bearer secret-token", "Cookie": "sb=1"},
        )
    assert r.status_code == 500
    sentry_sdk.flush()
    assert sentry_capture.events, "the error reached Sentry"
    dumped = json.dumps(sentry_capture.events)
    for word in (*HEALTH, "secret-token", "token=abc", "sb=1"):
        assert word not in dumped, word


# --- PostHog -----------------------------------------------------------------------------


@pytest.fixture
def fake_posthog(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(posthog, "_client", fake)
    return fake


def test_track_drops_unknown_props(fake_posthog, caplog):
    with caplog.at_level(logging.WARNING):
        track(
            ACC, "scan_completed", {"method": "label", "found": True, "reason": "allergen_contains"}
        )
    kwargs = fake_posthog.capture.call_args.kwargs
    assert kwargs["properties"] == {"method": "label", "found": True}
    assert "reason" in caplog.text  # the dropped key is named, never its value
    assert "allergen_contains" not in caplog.text


def test_track_ignores_unknown_event(fake_posthog, caplog):
    with caplog.at_level(logging.WARNING):
        track(ACC, "member_saved", {"conditions": "diabetes"})
    fake_posthog.capture.assert_not_called()
    assert "member_saved" in caplog.text and "diabetes" not in caplog.text


def test_distinct_id_is_hashed(fake_posthog):
    track(ACC, "app_opened")
    kwargs = fake_posthog.capture.call_args.kwargs
    assert kwargs["distinct_id"] == HASHED
    assert str(ACC) not in json.dumps(kwargs, default=str)


def test_track_drops_unsafe_values(fake_posthog):
    track(ACC, "voice_asked", {"language": "fr"})
    assert fake_posthog.capture.call_args.kwargs["properties"] == {}
    track(ACC, "scan_started", {"method": "Asha's diabetes scan"})
    assert fake_posthog.capture.call_args.kwargs["properties"] == {}
    track(ACC, "report_submitted", {"reason": "wrong_values"})
    assert fake_posthog.capture.call_args.kwargs["properties"] == {"reason": "wrong_values"}
    track(ACC, "report_submitted", {"reason": "allergen_contains"})
    assert fake_posthog.capture.call_args.kwargs["properties"] == {}
    track(ACC, "verdicts_shown", {"member_count": 3})
    assert fake_posthog.capture.call_args.kwargs["properties"] == {"member_count": 3}
    track(ACC, "verdicts_shown", {"member_count": True})  # bool is not a count
    assert fake_posthog.capture.call_args.kwargs["properties"] == {}


def test_track_is_noop_without_a_key(monkeypatch):
    monkeypatch.setattr(posthog, "_client", None)
    track(ACC, "app_opened")  # must not raise


def test_track_never_raises(fake_posthog):
    fake_posthog.capture.side_effect = RuntimeError("network")
    track(ACC, "app_opened")


def test_allowed_events_match_the_plan():
    assert ALLOWED_EVENTS == {
        "app_opened": set(),
        "scan_started": {"method"},
        "scan_completed": {"method", "found"},
        "verdicts_shown": {"member_count"},
        "meal_logged": set(),
        "voice_asked": {"language"},
        "report_submitted": {"reason"},
        "share_clicked": {"kind"},
        "account_deleted": set(),
        # F6: client events, names only (no properties).
        "meal_queued": set(),
        "meal_log_undone": set(),
        "meal_removed": set(),
        "share_result": set(),
        "share_weekly": set(),
        "compare_opened": set(),
        "compare_viewed": set(),
        "product_search": set(),
    }


@pytest.mark.parametrize(
    "event",
    [
        "meal_logged",
        "meal_queued",
        "meal_log_undone",
        "meal_removed",
        "share_result",
        "share_weekly",
        "compare_opened",
        "compare_viewed",
        "product_search",
    ],
)
def test_f6_events_are_sent_without_any_property(fake_posthog, event):
    track(ACC, event, {"query": "biscuit", "member_id": "x", "grams": 30})
    fake_posthog.capture.assert_called_once()
    assert fake_posthog.capture.call_args.kwargs["properties"] == {}


def test_no_health_words_in_the_allow_list():
    banned = {"condition", "allergen", "diet", "verdict_reason", "status", "nutrient", "name"}
    keys = {k for props in ALLOWED_EVENTS.values() for k in props} | set(ALLOWED_EVENTS)
    assert not {k for k in keys if any(b in k for b in banned)}

import hashlib
from unittest.mock import MagicMock

from app.core import observability
from app.core.config import Settings
from app.core.observability import scrub_event
from app.integrations import posthog


def test_scrub_event_removes_pii():
    event = {
        "request": {
            "data": {"allergies": ["peanut"]},
            "cookies": {"sb": "x"},
            "headers": {"Authorization": "Bearer t", "User-Agent": "ua"},
            "query_string": "a=1",
        },
        "user": {"id": "u1", "email": "a@b.c", "ip_address": "1.2.3.4"},
    }
    out = scrub_event(event, {})
    assert out is not None
    assert "data" not in out["request"]
    assert "cookies" not in out["request"]
    assert "Authorization" not in out["request"]["headers"]
    assert out["request"]["headers"]["User-Agent"] == "ua"
    assert "email" not in out["user"]
    assert "ip_address" not in out["user"]
    assert out["user"]["id"] == hashlib.sha256(b"u1").hexdigest()


def test_scrub_event_removes_frame_vars_extra_and_breadcrumbs():
    event = {
        "extra": {"member": {"conditions": ["diabetes"]}},
        "breadcrumbs": {"values": [{"message": "SELECT ... allergens"}]},
        "exception": {
            "values": [
                {"stacktrace": {"frames": [{"function": "f", "vars": {"allergies": "peanut"}}]}}
            ]
        },
        "threads": {"values": [{"stacktrace": {"frames": [{"vars": {"x": 1}}]}}]},
    }
    out = scrub_event(event, {})
    assert out is not None
    assert "extra" not in out and "breadcrumbs" not in out
    assert "vars" not in out["exception"]["values"][0]["stacktrace"]["frames"][0]
    assert out["exception"]["values"][0]["stacktrace"]["frames"][0]["function"] == "f"
    assert "vars" not in out["threads"]["values"][0]["stacktrace"]["frames"][0]


def test_init_passes_pii_safe_sentry_options(monkeypatch):
    calls = {}
    monkeypatch.setattr(observability.sentry_sdk, "init", lambda **kw: calls.update(kw))
    observability.init_observability(
        Settings(_env_file=None, environment="test", sentry_dsn="https://k@o0.ingest.sentry.io/1")
    )
    assert calls["send_default_pii"] is False
    assert calls["max_request_body_size"] == "never"
    assert calls["include_local_variables"] is False
    assert calls["max_breadcrumbs"] == 0
    assert calls["before_send"] is scrub_event
    assert calls["before_send_transaction"] is scrub_event


def test_scrub_event_without_request_or_user():
    assert scrub_event({"level": "error"}, {}) == {"level": "error"}


def test_scrub_event_redacts_the_top_level_message():
    """D1/S3: capture_message() and some integrations put free text in event["message"]."""
    event = {"message": "member Asha has diabetes, allergic to peanut", "level": "error"}
    out = scrub_event(event, {})
    assert out == {"message": "<redacted>", "level": "error"}


def test_scrub_event_redacts_a_structured_message():
    event = {"message": {"message": "bad %s", "params": ["diabetes"], "formatted": "bad diabetes"}}
    out = scrub_event(event, {})
    assert out["message"] == "<redacted>"
    assert "diabetes" not in str(out)


def test_init_without_keys_is_noop():
    observability.init_observability(Settings(_env_file=None, environment="test"))
    assert posthog._client is None


def test_scrub_event_redacts_exception_values_and_logentry():
    secret = "[parameters: {'conditions': ['diabetes']}]"
    event = {
        "exception": {
            "values": [
                {
                    "type": "IntegrityError",
                    "module": "sqlalchemy.exc",
                    "value": f"DETAIL: Failing row contains (x) {secret}",
                    "stacktrace": {"frames": [{"function": "f"}]},
                }
            ]
        },
        "logentry": {"message": "bad %s", "params": ["diabetes"], "formatted": "bad diabetes"},
    }
    out = scrub_event(event, {})
    exc = out["exception"]["values"][0]
    assert exc["value"] == "<redacted>"
    assert exc["type"] == "IntegrityError"
    assert exc["stacktrace"]["frames"] == [{"function": "f"}]
    assert "diabetes" not in str(out)


def test_shutdown_flushes_posthog(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(posthog, "_client", fake)
    observability.shutdown_observability()
    fake.shutdown.assert_called_once()
    assert posthog._client is None


async def test_lifespan_shuts_down_posthog(monkeypatch, app):
    fake = MagicMock()
    monkeypatch.setattr(posthog, "_client", fake)
    async with app.router.lifespan_context(app):
        pass
    fake.shutdown.assert_called_once()


def test_scrub_event_keeps_tags_so_redacted_alerts_stay_identifiable():
    event = {"message": "callmissed insufficient_credits", "tags": {"alert": "x"}}
    out = scrub_event(event, {})
    assert out["message"] == "<redacted>" and out["tags"] == {"alert": "x"}

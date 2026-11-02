from unittest.mock import MagicMock

from app.core import observability
from app.core.config import Settings
from app.core.observability import ALLOWED_EVENT_PROPS, capture, scrub_event


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
    assert out["user"]["id"] == "u1"


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
    assert calls["include_local_variables"] is False
    assert calls["max_breadcrumbs"] == 0
    assert calls["before_send"] is scrub_event
    assert calls["before_send_transaction"] is scrub_event


def test_scrub_event_without_request_or_user():
    assert scrub_event({"message": "x"}, {}) == {"message": "x"}


def test_capture_is_noop_without_key(monkeypatch):
    monkeypatch.setattr(observability, "_posthog", None)
    capture("e", "d", {"screen": "home"})  # must not raise


def test_capture_filters_properties(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(observability, "_posthog", fake)
    capture("e", "d", {"conditions": ["diabetes"], "screen": "home", "source": "api"})
    fake.capture.assert_called_once()
    kwargs = fake.capture.call_args.kwargs
    assert kwargs["properties"] == {"screen": "home", "source": "api"}
    assert kwargs["distinct_id"] == "d"


def test_allow_list():
    assert ALLOWED_EVENT_PROPS == {"platform", "locale", "screen", "status_code", "source"}


def test_init_without_keys_is_noop():
    observability.init_observability(Settings(_env_file=None, environment="test"))
    assert observability._posthog is None


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


def test_capture_constrains_values(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(observability, "_posthog", fake)
    capture(
        "e",
        "d",
        {
            "locale": "fr",
            "platform": "ios",
            "screen": "Diabetes Home",
            "source": "scan_page",
            "status_code": "200",
        },
    )
    assert fake.capture.call_args.kwargs["properties"] == {"source": "scan_page"}
    capture("e", "d", {"locale": "hi", "platform": "api", "screen": "home", "status_code": 404})
    assert fake.capture.call_args.kwargs["properties"] == {
        "locale": "hi",
        "platform": "api",
        "screen": "home",
        "status_code": 404,
    }


def test_shutdown_flushes_posthog(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(observability, "_posthog", fake)
    observability.shutdown_observability()
    fake.shutdown.assert_called_once()
    assert observability._posthog is None


async def test_lifespan_shuts_down_posthog(monkeypatch, app):
    fake = MagicMock()
    monkeypatch.setattr(observability, "_posthog", fake)
    async with app.router.lifespan_context(app):
        pass
    fake.shutdown.assert_called_once()

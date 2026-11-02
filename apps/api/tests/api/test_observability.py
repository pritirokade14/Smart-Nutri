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

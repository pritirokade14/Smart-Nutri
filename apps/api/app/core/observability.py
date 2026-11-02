"""Sentry and PostHog setup. No health data may reach either service."""

from typing import Any

import sentry_sdk
from posthog import Posthog

from app.core.config import Settings

# Same allow-list as the web (lib/analytics.ts) and Android (analytics.dart) clients.
ALLOWED_EVENT_PROPS = frozenset({"platform", "locale", "screen", "status_code", "source"})

# Hard-coded ingest host (US cloud); no env var by design.
POSTHOG_HOST = "https://us.i.posthog.com"

_posthog: Posthog | None = None


def scrub_event(event: dict, hint: dict) -> dict | None:
    """Sentry before_send / before_send_transaction.

    Drops request body, cookies, query string, auth headers, user email/IP/username,
    stack-frame local variables, `extra`, and breadcrumbs (which can hold SQL params or
    log messages with health data).
    """
    event.pop("extra", None)
    event.pop("breadcrumbs", None)
    for exc in (event.get("exception") or {}).get("values") or []:
        for frame in (exc.get("stacktrace") or {}).get("frames") or []:
            frame.pop("vars", None)
    for thread in (event.get("threads") or {}).get("values") or []:
        for frame in (thread.get("stacktrace") or {}).get("frames") or []:
            frame.pop("vars", None)
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("data", None)
        request.pop("cookies", None)
        request.pop("query_string", None)
        headers = request.get("headers")
        if isinstance(headers, dict):
            for key in list(headers):
                if key.lower() in {"authorization", "cookie", "x-api-key"}:
                    del headers[key]
    user = event.get("user")
    if isinstance(user, dict):
        user.pop("email", None)
        user.pop("ip_address", None)
        user.pop("username", None)
    return event


def init_observability(settings: Settings) -> None:
    global _posthog
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            send_default_pii=False,
            traces_sample_rate=0.1 if settings.environment == "prod" else 0.0,
            include_local_variables=False,
            max_breadcrumbs=0,
            before_send=scrub_event,
            before_send_transaction=scrub_event,
        )
    if settings.posthog_api_key and _posthog is None:
        _posthog = Posthog(
            settings.posthog_api_key,
            host=POSTHOG_HOST,
            disable_geoip=True,
        )


def capture(event: str, distinct_id: str, properties: dict[str, Any] | None = None) -> None:
    if _posthog is None:
        return
    safe = {k: v for k, v in (properties or {}).items() if k in ALLOWED_EVENT_PROPS}
    _posthog.capture(event, distinct_id=distinct_id, properties=safe)

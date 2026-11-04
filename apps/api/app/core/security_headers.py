"""Security headers on every API response (Plan 8 Task 6).

The API serves JSON only, so the policy is strict:
- nothing may be framed, sniffed or loaded;
- no referrer is sent;
- responses are `no-store` unless a route sets its own Cache-Control (the public product page
  does);
- HSTS is sent in prod only.

The interactive docs are off in prod (see `create_app`), so the strict CSP never breaks them.
"""

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_ALWAYS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "cross-origin-resource-policy": "same-site",
}
_JSON_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
_DOCS_PATHS = ("/docs", "/redoc")  # dev only: Swagger UI loads scripts from a CDN
HSTS = "max-age=31536000; includeSubDomains"


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, hsts: bool) -> None:
        self.app = app
        self.hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        docs = scope.get("path", "").startswith(_DOCS_PATHS)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in _ALWAYS.items():
                    headers[name] = value
                if not docs:
                    headers["content-security-policy"] = _JSON_CSP
                if "cache-control" not in headers:
                    headers["cache-control"] = "no-store"
                if self.hsts:
                    headers["strict-transport-security"] = HSTS
            await send(message)

        await self.app(scope, receive, send_with_headers)

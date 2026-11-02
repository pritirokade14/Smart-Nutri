import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

# Codes produced by the handlers below. Module-level so the error-code/i18n contract test
# (tests/unit/test_error_codes_i18n.py) can collect them.
VALIDATION_CODE = "validation_error"
INTERNAL_CODE = "internal_error"
HTTP_STATUS_CODES: dict[int, str] = {
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
}
HTTP_FALLBACK_CODE = "http_error"


class ErrorBody(BaseModel):
    """A stable `code`; clients localise `message_key` (always `error.<code>`)."""

    code: str
    message_key: str
    details: dict[str, Any]


class ErrorEnvelope(BaseModel):
    """The only error shape the API returns (never FastAPI's `{"detail": [...]}`)."""

    error: ErrorBody


# Documented on every operation via FastAPI(responses=...). The 422 entry also stops FastAPI
# from adding its default HTTPValidationError, which this API never returns.
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorEnvelope, "description": "Missing or invalid access token"},
    404: {"model": ErrorEnvelope, "description": "Not found"},
    422: {"model": ErrorEnvelope, "description": "Validation error"},
    429: {"model": ErrorEnvelope, "description": "Rate limited"},
    500: {"model": ErrorEnvelope, "description": "Internal error"},
}


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        status: int,
        message_key: str | None = None,
        details: dict | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(code)
        self.headers = dict(headers) if headers else None
        self.code = code
        self.status = status
        self.message_key = message_key or f"error.{code}"
        self.details = details or {}


def _envelope(
    status: int,
    code: str,
    message_key: str | None = None,
    details: dict | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorBody(
            code=code, message_key=message_key or f"error.{code}", details=details or {}
        )
    )
    return JSONResponse(
        status_code=status,
        headers=dict(headers) if headers else None,
        content=body.model_dump(mode="json"),
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _envelope(exc.status, exc.code, exc.message_key, exc.details, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [".".join(str(p) for p in e["loc"]) for e in exc.errors()]
        return _envelope(422, VALIDATION_CODE, details={"fields": fields})

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = HTTP_STATUS_CODES.get(exc.status_code, HTTP_FALLBACK_CODE)
        return _envelope(exc.status_code, code, headers=exc.headers)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled exception", exc_info=exc)
        return _envelope(500, INTERNAL_CODE)


class CatchAllMiddleware:
    """Innermost ASGI middleware: turns unhandled exceptions into the error envelope.

    Sits inside CORSMiddleware so 500 responses still carry CORS headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def tracking_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception as exc:
            if started:
                raise
            logger.error("unhandled exception", exc_info=exc)
            response = _envelope(500, INTERNAL_CODE)
            await response(scope, receive, send)

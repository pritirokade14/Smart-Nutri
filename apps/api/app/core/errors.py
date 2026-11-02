import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        status: int,
        message_key: str | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
        self.message_key = message_key or f"error.{code}"
        self.details = details or {}


def _envelope(
    status: int, code: str, message_key: str | None = None, details: dict | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message_key": message_key or f"error.{code}",
                "details": details or {},
            }
        },
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _envelope(exc.status, exc.code, exc.message_key, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [".".join(str(p) for p in e["loc"]) for e in exc.errors()]
        return _envelope(422, "validation_error", details={"fields": fields})

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return _envelope(404, "not_found")
        code = {401: "unauthorized", 403: "forbidden", 405: "method_not_allowed"}.get(
            exc.status_code, "http_error"
        )
        return _envelope(exc.status_code, code)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled exception", exc_info=exc)
        return _envelope(500, "internal_error")

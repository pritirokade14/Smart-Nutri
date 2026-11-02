import logging

from app.core.logging import configure_logging


def test_http_client_loggers_quiet_and_uvicorn_propagates():
    configure_logging("dev")
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        assert lg.propagate and not lg.handlers


def test_json_formatter_never_renders_exception_message():
    import json
    import sys

    from app.core.logging import JsonFormatter

    try:
        raise ValueError("[parameters: {'conditions': ['diabetes']}]")
    except ValueError:
        rec = logging.LogRecord(
            "x", logging.ERROR, "f", 1, "unhandled exception", None, sys.exc_info()
        )
    out = json.loads(JsonFormatter().format(rec))
    assert "diabetes" not in json.dumps(out)
    assert out["exc_type"] == "ValueError"

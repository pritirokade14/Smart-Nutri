import logging

from app.core.logging import configure_logging


def test_http_client_loggers_quiet_and_uvicorn_propagates():
    configure_logging("dev")
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        assert lg.propagate and not lg.handlers

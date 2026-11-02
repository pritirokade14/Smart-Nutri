import logging

from app.core.logging import configure_logging


def test_http_client_loggers_quiet_and_uvicorn_propagates():
    configure_logging("DEBUG")
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        assert lg.propagate and not lg.handlers


def test_log_level_defaults_to_info_even_in_dev(monkeypatch):
    from app.core.config import Settings
    from app.main import create_app

    monkeypatch.delenv("LOG_LEVEL", raising=False)
    settings = Settings(_env_file=None, environment="dev")
    assert settings.log_level == "INFO"
    create_app(settings)
    assert logging.getLogger().level == logging.INFO


def test_log_level_from_env(monkeypatch):
    from app.core.config import Settings
    from app.main import create_app

    monkeypatch.setenv("LOG_LEVEL", "debug")
    settings = Settings(_env_file=None, environment="prod")
    assert settings.log_level == "DEBUG"
    create_app(settings)
    assert logging.getLogger().level == logging.DEBUG
    configure_logging("INFO")


def test_invalid_log_level_rejected(monkeypatch):
    import pytest
    from pydantic import ValidationError

    from app.core.config import Settings

    monkeypatch.setenv("LOG_LEVEL", "LOUD")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


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

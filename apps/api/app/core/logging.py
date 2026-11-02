import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            # Type name only: exception text can contain SQL params or row contents.
            exc_type = record.exc_info[0]
            payload["exc_type"] = exc_type.__name__ if exc_type else "Exception"
        return json.dumps(payload, default=str)


def configure_logging(environment: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if environment == "dev" else logging.INFO)
    # Chatty HTTP client libraries can log URLs/headers at INFO/DEBUG; keep them quiet.
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
    # Route uvicorn's logs through the JSON root handler.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True

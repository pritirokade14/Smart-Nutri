"""An opaque keyset cursor over (updated_at, id), newest first (custom foods, recipes)."""

import base64
import json
from datetime import datetime
from uuid import UUID

from app.core.errors import ApiError


def encode_cursor(updated_at: datetime, row_id: UUID) -> str:
    raw = json.dumps({"t": updated_at.isoformat(), "i": str(row_id)}).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    """422 `validation_error` (`query.cursor`) for anything this module did not produce."""
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return datetime.fromisoformat(data["t"]), UUID(data["i"])
    except (ValueError, KeyError, TypeError):
        raise ApiError("validation_error", 422, details={"fields": ["query.cursor"]}) from None

from typing import Literal

from pydantic import BaseModel


class HealthOut(BaseModel):
    """`ok`/`ok` (200); `degraded`/`error` when the database is unreachable (503);
    `unavailable`/`schema_behind` when its Alembic revision is not this build's head (503)."""

    status: Literal["ok", "degraded", "unavailable"]
    database: Literal["ok", "error", "schema_behind"]

"""The Alembic revision this build of the API expects the database to be at.

Computed once at import from the bundled migration scripts (`alembic.ini` and `alembic/` are
copied into the Docker image next to `app/`). `/v1/health` compares it with the database's
`alembic_version`, so a deploy whose migrations have not run reports `schema_behind` (503)
instead of serving requests against an old schema. Order of operations: migrate, then merge.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

API_DIR = Path(__file__).resolve().parents[2]


def _expected_head() -> str:
    config = Config(str(API_DIR / "alembic.ini"))
    head = ScriptDirectory.from_config(config).get_current_head()  # raises on multiple heads
    if head is None:
        raise RuntimeError("no Alembic revisions found")
    return head


EXPECTED_ALEMBIC_HEAD: str = _expected_head()

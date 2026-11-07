"""The seed job runs on its own (`python -m app.jobs.seed_foods`), outside the app factory.
Every foreign key on the mapped tables must resolve in that fresh process, or the upsert
fails with NoReferencedTableError (seen on dev, 2026-11-07)."""

import subprocess
import sys

CHECK = """
import app.jobs.seed_foods  # noqa: F401
from app.db.base import Base
for table in Base.metadata.tables.values():
    for fk in table.foreign_keys:
        fk.column  # raises NoReferencedTableError when the target table is not registered
print("ok")
"""


def test_seed_job_registers_every_foreign_key_target():
    result = subprocess.run(
        [sys.executable, "-c", CHECK], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.strip() == "ok"

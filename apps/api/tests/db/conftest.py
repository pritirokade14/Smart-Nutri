"""Database test fixtures: a throwaway Postgres 17 with the Alembic baseline applied.

The database comes from ``TEST_DATABASE_URL`` when it is set (CI provides a
``postgres:17`` service). Otherwise a disposable ``postgres:17`` Docker container
is started for the session and removed afterwards. These tests drop every table,
so they refuse to run against a hosted Supabase project.
"""

import json
import os
import shutil
import subprocess
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import psycopg
import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command

API_DIR = Path(__file__).resolve().parents[2]

TABLES = {
    "accounts",
    "members",
    "consents",
    "products",
    "off_product_cache",
    "scans",
    "meal_logs",
    "product_reports",
    "rate_limit_counters",
    "explanation_cache",
}

_FORBIDDEN_HOSTS = ("supabase.co", "supabase.com", "pooler.supabase")
_IMAGE = "postgres:17"


def _assert_disposable(url: str) -> None:
    if any(h in url for h in _FORBIDDEN_HOSTS):
        raise RuntimeError("TEST_DATABASE_URL points at Supabase; DB tests drop every table")


def _wait_for_postgres(url: str, timeout: float = 60.0) -> None:
    plain = url.replace("postgresql+psycopg://", "postgresql://")
    deadline = time.monotonic() + timeout
    last: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with psycopg.connect(plain, connect_timeout=2) as conn:
                conn.execute("select 1")
            return
        except psycopg.OperationalError as exc:
            last = exc
            time.sleep(0.5)
    raise RuntimeError(f"test Postgres not ready after {timeout}s: {last}")


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    env_url = os.environ.get("TEST_DATABASE_URL")
    if env_url:
        _assert_disposable(env_url)
        try:
            _wait_for_postgres(env_url, timeout=5)
        except RuntimeError as exc:
            pytest.skip(f"TEST_DATABASE_URL is unreachable: {exc}")
        yield env_url
        return

    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("DB tests need Docker (or TEST_DATABASE_URL); docker not found")
    if subprocess.run([docker, "info"], capture_output=True, check=False).returncode != 0:
        pytest.skip("DB tests need Docker (or TEST_DATABASE_URL); Docker is not running")

    name = f"smartnutri-test-pg-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            docker,
            "run",
            "-d",
            "--rm",
            "--name",
            name,
            "-e",
            "POSTGRES_PASSWORD=postgres",
            "-p",
            "127.0.0.1::5432",
            _IMAGE,
        ],
        check=True,
        capture_output=True,
    )
    try:
        port = None
        for _ in range(50):
            out = subprocess.run(
                [docker, "port", name, "5432/tcp"], capture_output=True, text=True, check=False
            ).stdout.strip()
            if out:
                port = out.splitlines()[0].rsplit(":", 1)[1]
                break
            time.sleep(0.2)
        if port is None:
            raise RuntimeError("could not read the test Postgres port from Docker")
        url = f"postgresql+psycopg://postgres:postgres@127.0.0.1:{port}/postgres"
        _wait_for_postgres(url)
        # The image restarts Postgres once after init; wait for the final server.
        time.sleep(1)
        _wait_for_postgres(url)
        yield url
    finally:
        subprocess.run([docker, "rm", "-f", name], capture_output=True, check=False)


@pytest.fixture(scope="session")
def alembic_cfg(pg_url: str) -> Config:
    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", pg_url)
    return cfg


@pytest.fixture(scope="session")
def migrated(alembic_cfg: Config) -> Config:
    """Fresh schema per session: downgrade to base, then upgrade to head."""
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")
    return alembic_cfg


@pytest.fixture
async def db(migrated: Config, pg_url: str) -> AsyncIterator[AsyncConnection]:
    """A connection as the superuser inside a transaction that is always rolled back."""
    engine = create_async_engine(pg_url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            trans = await conn.begin()
            try:
                yield conn
            finally:
                await trans.rollback()
    finally:
        await engine.dispose()


@asynccontextmanager
async def as_user(db: AsyncConnection, user_id: uuid.UUID | None) -> AsyncIterator[None]:
    """Act as a Supabase ``authenticated`` user with the given JWT ``sub``."""
    claims = json.dumps({"sub": str(user_id), "role": "authenticated"}) if user_id else ""
    await db.execute(text("set local role authenticated"))
    await db.execute(text("select set_config('request.jwt.claims', :c, true)"), {"c": claims})
    try:
        yield
    finally:
        await db.execute(text("reset role"))
        await db.execute(text("select set_config('request.jwt.claims', '', true)"))


@asynccontextmanager
async def as_anon(db: AsyncConnection) -> AsyncIterator[None]:
    await db.execute(text("set local role anon"))
    try:
        yield
    finally:
        await db.execute(text("reset role"))


@dataclass(frozen=True)
class Seed:
    account: uuid.UUID
    member: uuid.UUID
    consent: uuid.UUID
    scan: uuid.UUID
    meal_log: uuid.UUID
    report: uuid.UUID


@dataclass(frozen=True)
class TwoAccounts:
    a: uuid.UUID
    b: uuid.UUID
    seed_a: Seed
    seed_b: Seed
    product: uuid.UUID
    off_barcode: str


async def _seed(db: AsyncConnection, label: str, product: uuid.UUID) -> Seed:
    ids = {k: uuid.uuid4() for k in ("account", "member", "consent", "scan", "meal_log", "report")}
    await db.execute(
        text("insert into accounts (id, display_name) values (:id, :n)"),
        {"id": ids["account"], "n": f"{label} account"},
    )
    await db.execute(
        text("insert into members (id, account_id, name, relation) values (:id, :acc, :n, 'self')"),
        {"id": ids["member"], "acc": ids["account"], "n": f"{label} member"},
    )
    await db.execute(
        text(
            "insert into consents (id, account_id, purpose, version) "
            "values (:id, :acc, 'health_data', 'v1')"
        ),
        {"id": ids["consent"], "acc": ids["account"]},
    )
    await db.execute(
        text(
            "insert into scans (id, account_id, product_id, image_sha256) "
            "values (:id, :acc, :p, :sha)"
        ),
        {"id": ids["scan"], "acc": ids["account"], "p": product, "sha": f"sha-{label}"},
    )
    await db.execute(
        text(
            "insert into meal_logs (id, account_id, member_id, product_id, grams, nutrients) "
            "values (:id, :acc, :m, :p, 30, '{}'::jsonb)"
        ),
        {"id": ids["meal_log"], "acc": ids["account"], "m": ids["member"], "p": product},
    )
    await db.execute(
        text(
            "insert into product_reports (id, product_id, account_id, reason) "
            "values (:id, :p, :acc, 'other')"
        ),
        {"id": ids["report"], "p": product, "acc": ids["account"]},
    )
    return Seed(**ids)


@pytest.fixture
async def two_accounts(db: AsyncConnection) -> TwoAccounts:
    """Accounts A and B, each with one row in every owned table (inserted as postgres)."""
    product = uuid.uuid4()
    await db.execute(
        text(
            "insert into products (id, barcode, name, category, source) "
            "values (:id, '8901234567890', 'Test biscuit', 'general', 'user')"
        ),
        {"id": product},
    )
    await db.execute(
        text("insert into off_product_cache (barcode, payload) values ('8900000000001', '{}')")
    )
    await db.execute(
        text(
            "insert into rate_limit_counters (key, bucket, window_start, count) "
            "values ('acc', 'label_scans', date_trunc('day', now()), 1)"
        )
    )
    await db.execute(
        text(
            "insert into explanation_cache (product_id, profile_hash, language, payload) "
            "values (:p, 'h', 'en', '{}')"
        ),
        {"p": product},
    )
    seed_a = await _seed(db, "A", product)
    seed_b = await _seed(db, "B", product)
    return TwoAccounts(
        a=seed_a.account,
        b=seed_b.account,
        seed_a=seed_a,
        seed_b=seed_b,
        product=product,
        off_barcode="8900000000001",
    )

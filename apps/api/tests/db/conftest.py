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
from sqlalchemy import create_engine, make_url, text
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
    "deleted_accounts",
    "account_user_types",
    "diary_goal_settings",
    "meal_slots",
    "diary_days",
    "household_units",
    "foods",
    "food_portions",
    "custom_foods",
    "recipes",
    "recipe_ingredients",
    "favourites",
}

_ALLOWED_HOSTS = ("127.0.0.1", "localhost", "::1", "postgres")
_IMAGE = "postgres:17"


def _assert_disposable(url: str) -> None:
    """Host allowlist: DB tests drop every table, so only local/CI Postgres is acceptable."""
    host = make_url(url).host
    if host not in _ALLOWED_HOSTS:
        raise RuntimeError(
            f"refusing to run DB tests against host {host!r}; allowed: {_ALLOWED_HOSTS}"
        )


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
    # env.py must never fall back to Settings/.env when run from tests.
    assert cfg.get_main_option("sqlalchemy.url") == pg_url
    return cfg


SUPABASE_DEFAULT_PRIVILEGES = """
DO $roles$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
    END IF;
END
$roles$;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
"""


def _assert_not_supabase(url: str) -> None:
    engine = create_engine(url, poolclass=NullPool)
    try:
        with engine.connect() as conn:
            if conn.execute(text("select to_regclass('auth.users') is not null")).scalar():
                raise RuntimeError("auth.users exists: this looks like Supabase; refusing")
    finally:
        engine.dispose()


def _emulate_supabase_default_privileges(url: str) -> None:
    engine = create_engine(url, poolclass=NullPool)
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(SUPABASE_DEFAULT_PRIVILEGES.replace("%", "%%"))
    finally:
        engine.dispose()


def _drop_alembic_version(url: str) -> None:
    engine = create_engine(url, poolclass=NullPool)
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("DROP TABLE IF EXISTS public.alembic_version")
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def migrated(alembic_cfg: Config) -> Config:
    """Fresh schema per session: downgrade to base, then upgrade to head."""
    url = alembic_cfg.get_main_option("sqlalchemy.url")
    _assert_not_supabase(url)
    command.downgrade(alembic_cfg, "base")
    # `downgrade base` creates alembic_version on a fresh DB; drop it so that it is
    # re-created by `upgrade` AFTER the default privileges exist, as on Supabase.
    _drop_alembic_version(url)
    # Reproduce Supabase: new public tables (incl. alembic_version) are granted ALL to
    # anon/authenticated/service_role. The migration must tighten this.
    _emulate_supabase_default_privileges(url)
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
    slot: uuid.UUID
    custom_food: uuid.UUID
    recipe: uuid.UUID
    ingredient: uuid.UUID
    favourite: uuid.UUID


@dataclass(frozen=True)
class TwoAccounts:
    a: uuid.UUID
    b: uuid.UUID
    seed_a: Seed
    seed_b: Seed
    product: uuid.UUID
    off_barcode: str


async def _seed(db: AsyncConnection, label: str, product: uuid.UUID) -> Seed:
    ids = {
        k: uuid.uuid4()
        for k in (
            "account",
            "member",
            "consent",
            "scan",
            "meal_log",
            "report",
            "slot",
            "custom_food",
            "recipe",
            "ingredient",
            "favourite",
        )
    }
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
    # One default slot per member (Plan 11, migration 0009); the entry below uses it.
    await db.execute(
        text(
            "insert into meal_slots (id, account_id, member_id, position, label_key, is_default) "
            "values (:id, :acc, :m, 0, 'diary.slot.breakfast', true)"
        ),
        {"id": ids["slot"], "acc": ids["account"], "m": ids["member"]},
    )
    await db.execute(
        text(
            "insert into meal_logs (id, account_id, member_id, product_id, grams, nutrients, "
            "local_date, meal_slot_id) "
            "values (:id, :acc, :m, :p, 30, '{}'::jsonb, current_date, :slot)"
        ),
        {
            "id": ids["meal_log"],
            "acc": ids["account"],
            "m": ids["member"],
            "p": product,
            "slot": ids["slot"],
        },
    )
    await db.execute(
        text(
            "insert into product_reports (id, product_id, account_id, reason) "
            "values (:id, :p, :acc, 'other')"
        ),
        {"id": ids["report"], "p": product, "acc": ids["account"]},
    )
    # One user-types row per account (Plan 9, P9-R1); its key is the account id.
    await db.execute(
        text(
            "insert into account_user_types (account_id, types, follow_ups) "
            """values (:acc, '{gym}', '{"gym_goal": "stay_fit"}'::jsonb)"""
        ),
        {"acc": ids["account"]},
    )
    # One goal-settings row per member (Plan 10, migration 0008); its key is the member id.
    await db.execute(
        text(
            "insert into diary_goal_settings (member_id, account_id, direction, activity_level) "
            "values (:m, :acc, 'maintain', 'light')"
        ),
        {"m": ids["member"], "acc": ids["account"]},
    )
    # One frozen day per member (Plan 11, migration 0009); its key is (member_id, local_date).
    await db.execute(
        text(
            "insert into diary_days (member_id, local_date, account_id, status) "
            "values (:m, current_date, :acc, 'none')"
        ),
        {"m": ids["member"], "acc": ids["account"]},
    )
    # One custom food, one recipe and one ingredient per account (Plan 12, migration 0011).
    await db.execute(
        text(
            "insert into custom_foods (id, account_id, name, basis, per_100, entered) "
            "values (:id, :acc, 'Own food', 'g', '{}'::jsonb, '{}'::jsonb)"
        ),
        {"id": ids["custom_food"], "acc": ids["account"]},
    )
    await db.execute(
        text(
            "insert into recipes (id, account_id, name, per_100g) "
            "values (:id, :acc, 'Own recipe', '{}'::jsonb)"
        ),
        {"id": ids["recipe"], "acc": ids["account"]},
    )
    await db.execute(
        text(
            "insert into recipe_ingredients (id, recipe_id, account_id, position, source_kind, "
            "custom_food_id, name, quantity, unit, grams, basis, per_100) "
            "values (:id, :r, :acc, 0, 'custom_food', :cf, 'Own food', 50, 'g', 50, 'g', "
            "'{}'::jsonb)"
        ),
        {
            "id": ids["ingredient"],
            "r": ids["recipe"],
            "acc": ids["account"],
            "cf": ids["custom_food"],
        },
    )
    # One favourite food per member (Plan 12 slice 5, migration 0012).
    await db.execute(
        text(
            "insert into favourites (id, account_id, member_id, kind, source_kind, "
            "custom_food_id, name) "
            "values (:id, :acc, :m, 'food', 'custom_food', :cf, 'Own food')"
        ),
        {
            "id": ids["favourite"],
            "acc": ids["account"],
            "m": ids["member"],
            "cf": ids["custom_food"],
        },
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
    # A tombstone of some earlier, erased account (D1/B1).
    await db.execute(text("insert into deleted_accounts (id) values (:id)"), {"id": uuid.uuid4()})
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

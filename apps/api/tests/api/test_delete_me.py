"""Plan 8 Task 2: DELETE /v1/me erases the account, its storage objects and its auth user."""

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.core.errors import ApiError
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me.service import ACCOUNT_OWNED_TABLES, ensure_account, erase_account_rows
from app.integrations import posthog
from app.integrations.storage import get_storage
from app.integrations.supabase_admin import get_supabase_admin
from tests.fakes.admin import FakeAdmin
from tests.fakes.storage import FakeStorage, missing_bucket_storage

A = UUID("11111111-1111-1111-1111-111111111111")
B = UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def storage() -> FakeStorage:
    """The label-photo bucket."""
    return FakeStorage(
        {
            f"{A}/{uuid4()}.jpg": b"a-label",
            f"{A}/{uuid4()}.png": b"a-orphan-upload",
            f"{B}/{uuid4()}.jpg": b"b-label",
        }
    )


@pytest.fixture
def admin() -> FakeAdmin:
    return FakeAdmin()


@pytest.fixture
def login(app, db_session, storage, admin):
    def _login(account_id: UUID = A) -> None:
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[current_account] = lambda: AccountContext(account_id, None)
        app.dependency_overrides[get_storage] = lambda: storage
        app.dependency_overrides[get_supabase_admin] = lambda: admin

    return _login


async def _exec(session, sql: str, **params):
    return await session.execute(text(sql), params)


async def seed(session, account_id: UUID, storage: FakeStorage) -> dict[str, UUID]:
    """One row in every account-owned table, plus a product the account contributed."""
    await ensure_account(session, AccountContext(account_id, None))
    product = (
        await _exec(
            session,
            "insert into products (name, source, created_by) values ('Biscuit', 'user', :a) "
            "returning id",
            a=account_id,
        )
    ).scalar_one()
    member = (
        await _exec(
            session,
            "insert into members (account_id, name, relation, allergens, conditions) "
            "values (:a, 'Asha', 'self', '{peanut}', '{diabetes}') returning id",
            a=account_id,
        )
    ).scalar_one()
    await _exec(
        session,
        "insert into consents (account_id, purpose, version) values (:a, 'health_data', 'v')",
        a=account_id,
    )
    image = next(p for p in storage.objects if p.startswith(f"{account_id}/"))
    await _exec(
        session,
        "insert into scans (account_id, product_id, image_path) values (:a, :p, :i)",
        a=account_id,
        p=product,
        i=image,
    )
    await _exec(
        session,
        "insert into meal_logs (account_id, member_id, product_id, grams, nutrients) "
        "values (:a, :m, :p, 30, '{}')",
        a=account_id,
        m=member,
        p=product,
    )
    await _exec(
        session,
        "insert into product_reports (product_id, account_id, reason) values (:p, :a, 'other')",
        a=account_id,
        p=product,
    )
    await _exec(
        session,
        "insert into rate_limit_counters (key, bucket, window_start, count) "
        "values (:k, 'analyze', now(), 3)",
        k=f"acct:{account_id}",
    )
    await _exec(
        session,
        "insert into account_user_types (account_id, types, active_type) "
        "values (:a, '{health_condition,gym}', 'gym')",
        a=account_id,
    )
    await session.flush()
    return {"product": product, "member": member}


async def counts(session, account_id: UUID) -> dict[str, int]:
    out = {}
    for table in ACCOUNT_OWNED_TABLES:
        out[table] = (
            await _exec(
                session, f"select count(*) from {table} where account_id = :a", a=account_id
            )
        ).scalar_one()
    out["accounts"] = (
        await _exec(session, "select count(*) from accounts where id = :a", a=account_id)
    ).scalar_one()
    # The account_deletes counter is kept on purpose until the tombstone is purged (D1/S5),
    # so that the DELETE limit still holds after an erasure.
    out["rate_limit_counters"] = (
        await _exec(
            session,
            "select count(*) from rate_limit_counters "
            "where key = :k and bucket <> 'account_deletes'",
            k=f"acct:{account_id}",
        )
    ).scalar_one()
    return out


async def tombstoned(session, account_id: UUID) -> bool:
    return (
        await _exec(session, "select count(*) from deleted_accounts where id = :a", a=account_id)
    ).scalar_one() == 1


async def test_delete_me_removes_all_rows(client, login, db_session, storage):
    await seed(db_session, A, storage)
    login(A)
    r = await client.delete("/v1/me")
    assert r.status_code == 204 and r.content == b""
    assert set((await counts(db_session, A)).values()) == {0}


async def test_delete_me_erases_user_types(client, login, db_session, storage):
    """Plan 9 (P9-R1): the user types (health-revealing) go with the account."""
    await seed(db_session, A, storage)
    await seed(db_session, B, storage)
    assert "account_user_types" in ACCOUNT_OWNED_TABLES
    # Erased before consents (the list is erased in order).
    order = list(ACCOUNT_OWNED_TABLES)
    assert order.index("account_user_types") < order.index("consents")
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    left = await _exec(
        db_session,
        "select account_id from account_user_types where account_id in (:a, :b)",
        a=A,
        b=B,
    )
    assert left.scalars().all() == [B]


async def test_delete_me_removes_storage_and_is_idempotent(
    client, login, db_session, storage, admin
):
    await seed(db_session, A, storage)
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    assert not [p for p in storage.objects if str(A) in p]
    assert len([p for p in storage.deleted if str(A) in p]) == 2  # label, orphan
    assert admin.deleted == [A]
    # Second call: nothing left to delete, auth user already gone (404 = success).
    r = await client.delete("/v1/me")
    assert r.status_code == 204
    assert set((await counts(db_session, A)).values()) == {0}


async def test_contributed_products_kept_without_owner(client, login, db_session, storage):
    ids = await seed(db_session, A, storage)
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    row = (
        await _exec(
            db_session, "select name, created_by from products where id = :p", p=ids["product"]
        )
    ).one()
    assert row.name == "Biscuit" and row.created_by is None


async def test_auth_admin_failure_returns_503_and_retry_succeeds(
    client, login, db_session, storage, admin
):
    await seed(db_session, A, storage)
    admin.failures = 1
    login(A)
    r = await client.delete("/v1/me")
    assert r.status_code == 503
    assert r.json()["error"] == {
        "code": "deletion_incomplete",
        "message_key": "error.deletion_incomplete",
        "details": {},
    }
    # The database and storage are already clean; only the auth user remains.
    assert set((await counts(db_session, A)).values()) == {0}
    assert not [p for p in storage.objects if str(A) in p]
    assert (await client.delete("/v1/me")).status_code == 204
    assert admin.deleted == [A]


async def test_storage_failure_returns_503_and_deletes_nothing(
    client, login, db_session, storage, admin
):
    await seed(db_session, A, storage)
    storage.unavailable = True
    login(A)
    r = await client.delete("/v1/me")
    assert r.status_code == 503 and r.json()["error"]["code"] == "deletion_incomplete"
    assert (await counts(db_session, A))["members"] == 1
    assert admin.deleted == []


def test_delete_me_never_touches_a_voice_bucket():
    """ADR 0020: no voice audio is stored, so erasure lists and deletes only label photos."""
    from fastapi.routing import APIRoute

    from app.features.me import service
    from app.features.me.router import router
    from app.integrations import storage

    assert not hasattr(storage, "get_voice_storage")
    assert not hasattr(service, "account_voice_paths")
    [route] = [r for r in router.routes if isinstance(r, APIRoute) and r.name == "me_delete"]
    assert [d.name for d in route.dependant.dependencies].count("storage") == 1
    assert "voice_storage" not in {d.name for d in route.dependant.dependencies}


async def test_other_accounts_data_untouched(client, login, db_session, storage):
    await seed(db_session, A, storage)
    await seed(db_session, B, storage)
    before = await counts(db_session, B)
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    assert await counts(db_session, B) == before
    assert len([p for p in storage.objects if str(B) in p]) == 1


async def test_delete_requires_auth(client):
    assert (await client.delete("/v1/me")).status_code == 401


async def test_every_account_owned_table_is_erased(db_session):
    """A new table with an account_id column must join ACCOUNT_OWNED_TABLES (Plans 6, 7...)."""
    tables = (
        await _exec(
            db_session,
            "select table_name from information_schema.columns "
            "where table_schema = 'public' and column_name = 'account_id'",
        )
    ).scalars()
    assert set(tables) <= set(ACCOUNT_OWNED_TABLES)


async def test_every_foreign_key_to_accounts_is_handled(db_session):
    """Columns referencing accounts.id are either erased (account_id) or nulled (created_by)."""
    refs = (
        await _exec(
            db_session,
            """
            select cl.relname as table_name, a.attname as column_name
            from pg_constraint c
            join pg_class cl on cl.oid = c.conrelid
            join pg_attribute a on a.attrelid = c.conrelid and a.attnum = any(c.conkey)
            where c.contype = 'f' and c.confrelid = 'public.accounts'::regclass
            """,
        )
    ).all()
    for table, column in refs:
        assert (column == "account_id" and table in ACCOUNT_OWNED_TABLES) or (
            table,
            column,
        ) == ("products", "created_by"), (table, column)


def test_openapi_documents_me_delete(app):
    op = app.openapi()["paths"]["/v1/me"]["delete"]
    assert op["operationId"] == "me_delete"
    assert "204" in op["responses"] and "503" in op["responses"]


async def test_deletion_sends_only_the_allow_listed_event(client, login, monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(posthog, "_client", fake)
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    fake.capture.assert_called_once_with(
        "account_deleted", distinct_id=posthog.hashed_id(A), properties={}
    )


# --- D1/B1: the deletion tombstone ---------------------------------------------------------

_AUTH_INVALID = {"code": "auth_invalid", "message_key": "error.auth_invalid", "details": {}}


async def test_deleted_account_is_locked_out_and_nothing_is_recreated(
    client, login, db_session, storage
):
    """A still-valid access token of an erased account gets 401 everywhere, and no row comes
    back: not the account (with its email-derived name), not a member, not a counter."""
    await seed(db_session, A, storage)
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    assert await tombstoned(db_session, A)

    for method, url, body in (
        ("GET", "/v1/me", None),
        ("GET", "/v1/members", None),
        ("POST", "/v1/members", {"name": "Asha", "relation": "child", "birth_year": 2018}),
        ("GET", "/v1/consents", None),
        ("POST", "/v1/consents", {"purpose": "terms", "version": "2026-11-01", "granted": True}),
        ("POST", "/v1/analyze", {}),  # consent-gated and rate-limited
        ("GET", "/v1/products/barcode/8901234567890", None),  # rate-limited only
    ):
        r = await client.request(method, url, json=body)
        assert r.status_code == 401, (method, url, r.text)
        assert r.json()["error"] == _AUTH_INVALID, (method, url)
        assert r.headers["www-authenticate"] == 'Bearer error="invalid_token"'

    assert set((await counts(db_session, A)).values()) == {0}


async def test_ensure_account_refuses_a_tombstoned_id(db_session):
    await ensure_account(db_session, AccountContext(A, "priya@example.com"))
    await erase_account_rows(db_session, A)
    await db_session.commit()
    with pytest.raises(ApiError) as exc_info:
        await ensure_account(db_session, AccountContext(A, "priya@example.com"))
    assert (exc_info.value.code, exc_info.value.status) == ("auth_invalid", 401)
    assert (await counts(db_session, A))["accounts"] == 0


async def test_tombstone_is_written_in_the_erasure_transaction(db_session, storage):
    await seed(db_session, A, storage)
    await db_session.commit()
    await erase_account_rows(db_session, A)
    assert await tombstoned(db_session, A)  # staged with the erasure, before the commit
    await db_session.rollback()
    # Rolled back together: the rows are back and there is no tombstone.
    assert not await tombstoned(db_session, A)
    assert (await counts(db_session, A))["members"] == 1


async def test_storage_failure_writes_no_tombstone(client, login, db_session, storage):
    await seed(db_session, A, storage)
    storage.unavailable = True
    login(A)
    assert (await client.delete("/v1/me")).status_code == 503
    assert not await tombstoned(db_session, A)
    assert (await client.get("/v1/me")).status_code == 200  # the account still works


async def test_retry_after_auth_failure_still_erases_and_refreshes_the_tombstone(
    client, login, db_session, storage, admin
):
    await seed(db_session, A, storage)
    admin.failures = 1
    login(A)
    assert (await client.delete("/v1/me")).status_code == 503
    assert await tombstoned(db_session, A)  # rows are gone, so the tombstone is in place
    await _exec(
        db_session,
        "update deleted_accounts set deleted_at = now() - interval '3 days' where id = :a",
        a=A,
    )
    # The retry is allowed (the auth user is still there) and restarts the 7-day window:
    # the sign-in could still mint tokens until the auth user was removed.
    assert (await client.delete("/v1/me")).status_code == 204
    assert admin.deleted == [A]
    fresh = (
        await _exec(
            db_session,
            "select deleted_at > now() - interval '1 minute' from deleted_accounts where id = :a",
            a=A,
        )
    ).scalar_one()
    assert fresh is True


async def test_other_account_is_not_locked_out(client, login, db_session, storage):
    await seed(db_session, A, storage)
    await seed(db_session, B, storage)
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    login(B)
    assert (await client.get("/v1/me")).status_code == 200
    assert (await client.get("/v1/members")).status_code == 200


# --- D1/S5: rate limits on deletion and consents ----------------------------------------------


async def test_delete_me_is_rate_limited_per_day(app, client, login, db_session):
    app.state.settings.rate_limit_account_deletes_per_day = 2
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    assert (await client.delete("/v1/me")).status_code == 204
    r = await client.delete("/v1/me")
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
    assert int(r.headers["retry-after"]) >= 1


def test_default_deletion_and_consent_limits():
    from app.core.config import Settings

    settings = Settings(_env_file=None)
    assert settings.rate_limit_account_deletes_per_day == 5
    assert settings.rate_limit_consents_per_day == 60


async def test_consents_record_is_rate_limited_per_day(app, client, login, db_session):
    app.state.settings.rate_limit_consents_per_day = 2
    login(A)
    body = {"purpose": "terms", "version": "2026-11-01", "granted": True}
    assert (await client.post("/v1/consents", json=body)).status_code == 200
    assert (await client.post("/v1/consents", json=body)).status_code == 200
    r = await client.post("/v1/consents", json=body)
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
    # Reading consent state is not limited.
    assert (await client.get("/v1/consents")).status_code == 200


# --- m2: the tombstone records whether the auth user was removed ----------------------------


async def auth_deleted_at(session, account_id: UUID):
    return (
        await _exec(
            session, "select auth_deleted_at from deleted_accounts where id = :a", a=account_id
        )
    ).scalar_one()


async def test_successful_deletion_marks_the_auth_user_removed(client, login, db_session, storage):
    await seed(db_session, A, storage)
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    assert await auth_deleted_at(db_session, A) is not None


async def test_auth_failure_leaves_the_tombstone_unmarked_until_a_retry(
    client, login, db_session, storage, admin
):
    await seed(db_session, A, storage)
    admin.failures = 1
    login(A)
    assert (await client.delete("/v1/me")).status_code == 503
    assert await auth_deleted_at(db_session, A) is None  # retention must not purge it yet
    assert (await client.delete("/v1/me")).status_code == 204
    assert await auth_deleted_at(db_session, A) is not None


# --- C1: a bucket that does not exist holds nothing to delete ---------------------------------


async def test_delete_me_succeeds_when_the_bucket_is_missing(
    app, client, login, db_session, storage, admin
):
    await seed(db_session, A, storage)  # its scan row still points at a label photo path
    login(A)
    app.dependency_overrides[get_storage] = lambda: missing_bucket_storage("label-photos")
    r = await client.delete("/v1/me")
    assert r.status_code == 204
    assert set((await counts(db_session, A)).values()) == {0}
    assert await tombstoned(db_session, A)
    assert admin.deleted == [A]

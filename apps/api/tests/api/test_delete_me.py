"""Plan 8 Task 2: DELETE /v1/me erases the account, its storage objects and its auth user."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me.service import ACCOUNT_OWNED_TABLES, ensure_account
from app.integrations.storage import get_storage
from app.integrations.supabase_admin import AdminUnavailable, get_supabase_admin
from tests.fakes.storage import FakeStorage

A = UUID("11111111-1111-1111-1111-111111111111")
B = UUID("22222222-2222-2222-2222-222222222222")


class FakeAdmin:
    def __init__(self, failures: int = 0) -> None:
        self.failures = failures
        self.deleted: list[UUID] = []
        self.gone: set[UUID] = set()

    async def delete_user(self, user_id: UUID) -> None:
        if self.failures:
            self.failures -= 1
            raise AdminUnavailable("fake outage")
        self.deleted.append(user_id)
        self.gone.add(user_id)


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage(
        {
            f"{A}/{uuid4()}.jpg": b"a-label",
            f"{A}/{uuid4()}.png": b"a-orphan-upload",
            f"voice/{A}/{uuid4()}.mp3": b"a-voice",
            f"{B}/{uuid4()}.jpg": b"b-label",
            f"voice/{B}/{uuid4()}.mp3": b"b-voice",
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
    out["rate_limit_counters"] = (
        await _exec(
            session,
            "select count(*) from rate_limit_counters where key = :k",
            k=f"acct:{account_id}",
        )
    ).scalar_one()
    return out


async def test_delete_me_removes_all_rows(client, login, db_session, storage):
    await seed(db_session, A, storage)
    login(A)
    r = await client.delete("/v1/me")
    assert r.status_code == 204 and r.content == b""
    assert set((await counts(db_session, A)).values()) == {0}


async def test_delete_me_removes_storage_and_is_idempotent(
    client, login, db_session, storage, admin
):
    await seed(db_session, A, storage)
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    assert not [p for p in storage.objects if str(A) in p]
    assert len([p for p in storage.deleted if str(A) in p]) == 3  # label, orphan, voice
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


async def test_other_accounts_data_untouched(client, login, db_session, storage):
    await seed(db_session, A, storage)
    await seed(db_session, B, storage)
    before = await counts(db_session, B)
    login(A)
    assert (await client.delete("/v1/me")).status_code == 204
    assert await counts(db_session, B) == before
    assert len([p for p in storage.objects if str(B) in p]) == 2


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

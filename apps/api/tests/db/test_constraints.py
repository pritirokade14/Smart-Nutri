"""Cascade behaviour on account deletion and member range checks."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


async def test_deleting_account_cascades(db, two_accounts):
    a, b = two_accounts.a, two_accounts.b
    # A created a product; it must survive with created_by NULL.
    await db.execute(
        text("update products set created_by = :a where id = :p"),
        {"a": a, "p": two_accounts.product},
    )
    await db.execute(text("delete from accounts where id = :a"), {"a": a})
    for table in ("members", "consents", "scans", "meal_logs", "product_reports"):
        n = (
            await db.execute(text(f"select count(*) from {table} where account_id = :a"), {"a": a})
        ).scalar()
        assert n == 0, table
        n = (
            await db.execute(text(f"select count(*) from {table} where account_id = :b"), {"b": b})
        ).scalar()
        assert n == 1, table
    created_by = (
        await db.execute(
            text("select created_by from products where id = :p"), {"p": two_accounts.product}
        )
    ).scalar()
    assert created_by is None


async def _insert_member(db, account, **cols):
    names = ", ".join(["account_id", "name", "relation", *cols])
    vals = ", ".join([":acc", "'m'", "'self'", *(f":{c}" for c in cols)])
    async with db.begin_nested():
        await db.execute(
            text(f"insert into members ({names}) values ({vals})"), {"acc": account, **cols}
        )


@pytest.mark.parametrize(
    ("col", "value"),
    [
        ("birth_year", 1899),
        ("birth_year", 2101),
        ("height_cm", 0),
        ("height_cm", -5),
        ("height_cm", 300.5),
        ("weight_kg", 0),
        ("weight_kg", -1),
        ("weight_kg", 500.5),
    ],
)
async def test_member_out_of_range_rejected(db, two_accounts, col, value):
    with pytest.raises(IntegrityError) as exc_info:
        await _insert_member(db, two_accounts.a, **{col: value})
    assert f"ck_members_{col}" in str(exc_info.value)


@pytest.mark.parametrize(
    "cols",
    [
        {"birth_year": 1900},
        {"birth_year": 2100},
        {"height_cm": 300},
        {"height_cm": 0.1},
        {"weight_kg": 500},
        {"weight_kg": 0.1},
        {},
    ],
)
async def test_member_in_range_accepted(db, two_accounts, cols):
    await _insert_member(db, two_accounts.a, **cols)


# R21(d): one scan per uploaded photo path per account.


async def _insert_scan(db, account, path):
    async with db.begin_nested():
        await db.execute(
            text("insert into scans (account_id, image_path) values (:a, :p)"),
            {"a": account, "p": path},
        )


async def test_scan_image_path_unique_per_account(db, two_accounts):
    path = f"{two_accounts.a}/photo.jpg"
    await _insert_scan(db, two_accounts.a, path)
    with pytest.raises(IntegrityError) as exc_info:
        await _insert_scan(db, two_accounts.a, path)
    assert "uq_scans_account_id_image_path" in str(exc_info.value)
    await _insert_scan(db, two_accounts.b, path)  # another account: a different key


async def test_scans_without_a_path_are_not_constrained(db, two_accounts):
    await _insert_scan(db, two_accounts.a, None)
    await _insert_scan(db, two_accounts.a, None)


async def test_members_body_fat_check(db, two_accounts):
    for bad in (2.9, 70.1):
        with pytest.raises(IntegrityError) as exc_info:
            await _insert_member(db, two_accounts.a, body_fat_pct=bad)
        assert "ck_members_body_fat_pct" in str(exc_info.value)
    for ok in (3, 70, 15.5):
        await _insert_member(db, two_accounts.a, body_fat_pct=ok)
    await _insert_member(db, two_accounts.a)  # null is unknown


async def test_diary_goal_settings_composite_fk_rejects_foreign_member(db, two_accounts):
    # Account A's row pointing at account B's member: the composite FK refuses it.
    b_member = await db.scalar(
        text(
            "insert into members (account_id, name, relation) "
            "values (:b, 'b2', 'other') returning id"
        ),
        {"b": two_accounts.b},
    )
    with pytest.raises(IntegrityError) as exc_info:
        async with db.begin_nested():
            await db.execute(
                text(
                    "insert into diary_goal_settings (member_id, account_id, direction, "
                    "activity_level) values (:m, :a, 'lose', 'light')"
                ),
                {"m": b_member, "a": two_accounts.a},
            )
    assert "fk_diary_goal_settings_member_id_members" in str(exc_info.value)


@pytest.mark.parametrize(
    ("col", "value", "constraint"),
    [
        ("direction", "cut", "ck_diary_goal_settings_direction"),
        ("activity_level", "extreme", "ck_diary_goal_settings_activity_level"),
        ("energy_mode", "magic", "ck_diary_goal_settings_energy_mode"),
        ("numbers_display", "hide_some", "ck_diary_goal_settings_numbers_display"),
        ("summary_view", "both", "ck_diary_goal_settings_summary_view"),
        ("sex_reference", "x", "ck_diary_goal_settings_sex_reference"),
        ("target_weight_kg", 1.9, "ck_diary_goal_settings_target_weight_kg"),
        ("target_weight_kg", 300.1, "ck_diary_goal_settings_target_weight_kg"),
    ],
)
async def test_diary_goal_settings_closed_sets(db, two_accounts, col, value, constraint):
    a = two_accounts
    member = await db.scalar(
        text(
            "insert into members (account_id, name, relation) values (:a, 'm2', 'other') returning id"
        ),
        {"a": a.a},
    )
    cols = {"direction": "maintain", "activity_level": "light", col: value}
    names = ", ".join(["member_id", "account_id", *cols])
    vals = ", ".join([":m", ":a", *(f":{c}" for c in cols)])
    with pytest.raises(IntegrityError) as exc_info:
        async with db.begin_nested():
            await db.execute(
                text(f"insert into diary_goal_settings ({names}) values ({vals})"),
                {"m": member, "a": a.a, **cols},
            )
    assert constraint in str(exc_info.value)


async def test_diary_goal_settings_defaults_and_cascade(db, two_accounts):
    row = (
        await db.execute(
            text(
                "select pregnant_or_breastfeeding, energy_mode, numbers_display, summary_view, "
                "rate_pct_bw_per_week, created_at is not null as c from diary_goal_settings "
                "where member_id = :m"
            ),
            {"m": two_accounts.seed_a.member},
        )
    ).one()
    assert tuple(row) == (False, "formula", "show", "remaining", None, True)
    # Deleting the member removes its settings (composite FK, ON DELETE CASCADE).
    await db.execute(text("delete from members where id = :m"), {"m": two_accounts.seed_a.member})
    n = await db.scalar(
        text("select count(*) from diary_goal_settings where account_id = :a"),
        {"a": two_accounts.a},
    )
    assert n == 0

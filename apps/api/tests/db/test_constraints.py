"""Cascade behaviour on account deletion and member range checks."""

import uuid

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


# ---- Plan 11 (migration 0009): meal slots and diary entries


async def _slot(db, seed, **cols):
    values = {"account_id": seed.account, "member_id": seed.member, "position": 5, **cols}
    names = ", ".join(values)
    params = ", ".join(f":{k}" for k in values)
    async with db.begin_nested():
        await db.execute(text(f"insert into meal_slots ({names}) values ({params})"), values)


async def _entry(db, seed, product, **cols):
    values = {
        "account_id": seed.account,
        "member_id": seed.member,
        "product_id": product,
        "grams": 30,
        "source_kind": "product",
        "local_date": "2026-11-07",
        "meal_slot_id": seed.slot,
        **cols,
    }
    names = ", ".join(values)
    params = ", ".join(f":{k}" for k in values)
    async with db.begin_nested():
        await db.execute(
            text(f"insert into meal_logs ({names}, nutrients) values ({params}, '{{}}')"), values
        )


@pytest.mark.parametrize(
    "cols",
    [
        {"product_id": None},  # product without a product_id
        {"source_kind": "off", "off_barcode": "8901"},  # off with both refs
        {"source_kind": "quick_add", "product_id": None, "grams": 30},  # quick_add with grams
        {"source_kind": "off", "product_id": None, "off_barcode": "8901", "grams": None},
        {"source_kind": "mystery"},
    ],
)
async def test_meal_logs_ref_per_kind(db, two_accounts, cols):
    with pytest.raises(IntegrityError) as exc_info:
        await _entry(db, two_accounts.seed_a, two_accounts.product, **cols)
    assert "ck_meal_logs_ref" in str(exc_info.value) or "ck_meal_logs_source_kind" in str(
        exc_info.value
    )


async def test_quick_add_row_allowed(db, two_accounts):
    await _entry(
        db,
        two_accounts.seed_a,
        None,
        source_kind="quick_add",
        grams=None,
        product_name="Evening chai",
    )


async def test_meal_slot_label_31_chars_refused(db, two_accounts):
    await _slot(db, two_accounts.seed_a, custom_label="x" * 30)
    with pytest.raises(IntegrityError) as exc_info:
        await _slot(db, two_accounts.seed_a, position=6, custom_label="y" * 31)
    assert "ck_meal_slots_custom_label_length" in str(exc_info.value)


async def test_meal_slot_needs_a_label(db, two_accounts):
    with pytest.raises(IntegrityError) as exc_info:
        await _slot(db, two_accounts.seed_a)
    assert "ck_meal_slots_label_present" in str(exc_info.value)


async def test_entry_cannot_use_other_members_slot(db, two_accounts):
    with pytest.raises(IntegrityError) as exc_info:
        await _entry(
            db,
            two_accounts.seed_a,
            two_accounts.product,
            meal_slot_id=two_accounts.seed_b.slot,
        )
    assert "fk_meal_logs_meal_slot_id_meal_slots" in str(exc_info.value)


async def test_used_slot_hard_delete_fails(db, two_accounts):
    with pytest.raises(IntegrityError) as exc_info:
        async with db.begin_nested():
            await db.execute(
                text("delete from meal_slots where id = :s"), {"s": two_accounts.seed_a.slot}
            )
    assert "fk_meal_logs_meal_slot_id_meal_slots" in str(exc_info.value)


async def test_member_delete_cascades_slots_and_entries(db, two_accounts):
    """Ruling E3: NO ACTION (not RESTRICT), so a member with entries and slots can go."""
    m = two_accounts.seed_a.member
    await db.execute(text("delete from members where id = :m"), {"m": m})
    for table in ("meal_slots", "meal_logs", "diary_days"):
        n = await db.scalar(text(f"select count(*) from {table} where member_id = :m"), {"m": m})
        assert n == 0, table


async def test_default_slot_unique_per_member(db, two_accounts):
    with pytest.raises(IntegrityError) as exc_info:
        await _slot(
            db, two_accounts.seed_a, label_key="diary.slot.breakfast", is_default=True, position=7
        )
    assert "uq_meal_slots_member_default" in str(exc_info.value)


async def test_active_label_unique_case_insensitive(db, two_accounts):
    seed = two_accounts.seed_a
    await _slot(db, seed, custom_label="Pre-workout")
    with pytest.raises(IntegrityError) as exc_info:
        await _slot(db, seed, position=6, custom_label="PRE-WORKOUT")
    assert "uq_meal_slots_member_label" in str(exc_info.value)
    # An archived duplicate is allowed; so is the same label for another member.
    await _slot(db, seed, position=7, custom_label="pre-workout", archived_at="2026-11-01")
    await _slot(db, two_accounts.seed_b, custom_label="Pre-workout")


async def test_diary_days_checks(db, two_accounts):
    seed = two_accounts.seed_a
    for col, value, name in (
        ("status", "bad", "ck_diary_days_status"),
        ("basis", "magic", "ck_diary_days_basis"),
        ("direction", "up", "ck_diary_days_direction"),
    ):
        cols = {"status": "none", col: value}
        names = ", ".join(["member_id", "local_date", "account_id", *cols])
        params = ", ".join([":m", "date '2020-01-01'", ":a", *(f":{c}" for c in cols)])
        with pytest.raises(IntegrityError) as exc_info:
            async with db.begin_nested():
                await db.execute(
                    text(f"insert into diary_days ({names}) values ({params})"),
                    {"m": seed.member, "a": seed.account, **cols},
                )
        assert name in str(exc_info.value)


# ---- Plan 12 Task 1 (migration 0010): food entries, units and portions


async def _food(db, code: str = "c-1") -> object:
    return (
        await db.execute(
            text(
                "insert into foods (source, source_code, name_en, search_text, basis, per_100, "
                "licence, data_version) values ('usda_fdc', :c, 'Dal', 'dal', 'g', '{}', "
                "'CC0 1.0', 'v') returning id"
            ),
            {"c": code},
        )
    ).scalar_one()


async def test_food_entry_needs_food_id_and_grams(db, two_accounts):
    seed = two_accounts.seed_a
    food = await _food(db)
    await _entry(
        db, seed, None, source_kind="food", food_id=food, grams=142, quantity=1, unit="katori"
    )
    for cols in (
        {"food_id": None},  # no food id
        {"grams": None},  # no grams
        {"product_id": two_accounts.product},  # a food row with a product id too
    ):
        values = {"source_kind": "food", "food_id": food, "grams": 142} | cols
        with pytest.raises(IntegrityError) as exc_info:
            await _entry(db, seed, values.pop("product_id", None), **values)
        assert "ck_meal_logs_ref" in str(exc_info.value)


async def test_product_entry_rejects_food_id(db, two_accounts):
    food = await _food(db)
    with pytest.raises(IntegrityError) as exc_info:
        await _entry(db, two_accounts.seed_a, two_accounts.product, food_id=food)
    assert "ck_meal_logs_ref" in str(exc_info.value)


@pytest.mark.parametrize("cols", [{"quantity": 1}, {"unit": "katori"}])
async def test_quantity_and_unit_together(db, two_accounts, cols):
    with pytest.raises(IntegrityError) as exc_info:
        await _entry(db, two_accounts.seed_a, two_accounts.product, **cols)
    assert "ck_meal_logs_quantity_unit" in str(exc_info.value)
    await _entry(db, two_accounts.seed_a, two_accounts.product, quantity=2, unit="piece")
    with pytest.raises(IntegrityError) as exc_info:
        await _entry(db, two_accounts.seed_a, two_accounts.product, quantity=5001, unit="g")
    assert "ck_meal_logs_quantity" in str(exc_info.value)


async def test_unit_must_exist(db, two_accounts):
    with pytest.raises(IntegrityError) as exc_info:
        await _entry(db, two_accounts.seed_a, two_accounts.product, quantity=1, unit="ladle")
    assert "fk_meal_logs_unit_household_units" in str(exc_info.value)
    food = await _food(db)
    with pytest.raises(IntegrityError) as exc_info:
        async with db.begin_nested():
            await db.execute(
                text(
                    "insert into food_portions (food_id, unit, grams_per_unit, source) "
                    "values (:f, 'handful', 30, 'reference_table')"
                ),
                {"f": food},
            )
    assert "fk_food_portions_unit_household_units" in str(exc_info.value)


async def _portion(db, **cols) -> None:
    values = {"unit": "roti", "grams_per_unit": 40, "source": "reference_table"} | cols
    names = ", ".join(values)
    params = ", ".join(f":{k}" for k in values)
    async with db.begin_nested():
        await db.execute(text(f"insert into food_portions ({names}) values ({params})"), values)


async def test_portion_exactly_one_ref(db, two_accounts):
    food = await _food(db)
    for cols in (
        {},  # no ref
        {"food_id": food, "product_id": two_accounts.product},
        {"food_id": food, "off_barcode": "8901"},
    ):
        with pytest.raises(IntegrityError) as exc_info:
            await _portion(db, **cols)
        assert "ck_food_portions_ref" in str(exc_info.value)
    await _portion(db, food_id=food)
    await _portion(db, off_barcode="8901", unit="piece")
    await _portion(db, product_id=two_accounts.product, unit="slice")
    with pytest.raises(IntegrityError) as exc_info:
        await _portion(db, food_id=food, unit="piece", grams_per_unit=2001)
    assert "ck_food_portions_grams" in str(exc_info.value)


async def test_global_portion_not_user_source(db, two_accounts):
    food = await _food(db)
    with pytest.raises(IntegrityError) as exc_info:
        await _portion(db, food_id=food, source="user")  # global row with source user
    assert "ck_food_portions_owner" in str(exc_info.value)
    with pytest.raises(IntegrityError) as exc_info:
        await _portion(db, food_id=food, account_id=two_accounts.a)  # user row, global source
    assert "ck_food_portions_owner" in str(exc_info.value)
    await _portion(db, food_id=food, account_id=two_accounts.a, source="user")


async def test_portion_unique_per_owner_ref_unit(db, two_accounts):
    food = await _food(db)
    a, b = two_accounts.a, two_accounts.b
    await _portion(db, food_id=food)  # global
    await _portion(db, food_id=food, account_id=a, source="user")  # A's override
    await _portion(db, food_id=food, account_id=b, source="user")  # B's override
    for cols, name in (
        ({"food_id": food}, "uq_food_portions_food"),
        ({"food_id": food, "account_id": a, "source": "user"}, "uq_food_portions_food"),
    ):
        with pytest.raises(IntegrityError) as exc_info:
            await _portion(db, **cols)
        assert name in str(exc_info.value)
    await _portion(db, off_barcode="8902")
    with pytest.raises(IntegrityError) as exc_info:
        await _portion(db, off_barcode="8902")
    assert "uq_food_portions_off" in str(exc_info.value)
    await _portion(db, product_id=two_accounts.product)
    with pytest.raises(IntegrityError) as exc_info:
        await _portion(db, product_id=two_accounts.product)
    assert "uq_food_portions_product" in str(exc_info.value)


# ---- Plan 12 slice 4 (migration 0011): custom foods, recipes, ingredients


async def _custom_food(db, account, **cols) -> object:
    values = {
        "account_id": account,
        "name": "Own bar",
        "basis": "g",
        "per_100": "{}",
        "entered": "{}",
    } | cols
    names = ", ".join(values)
    params = ", ".join(
        f"CAST(:{k} AS jsonb)" if k in ("per_100", "entered") else f":{k}" for k in values
    )
    async with db.begin_nested():
        return (
            await db.execute(
                text(f"insert into custom_foods ({names}) values ({params}) returning id"), values
            )
        ).scalar_one()


async def test_custom_food_barcode_unique_per_account(db, two_accounts):
    a, b = two_accounts.a, two_accounts.b
    await _custom_food(db, a, barcode="8901000000017")
    with pytest.raises(IntegrityError) as exc_info:
        await _custom_food(db, a, barcode="8901000000017")
    assert "uq_custom_foods_account_id_barcode" in str(exc_info.value)
    await _custom_food(db, b, barcode="8901000000017")  # another account: its own
    await _custom_food(db, a)  # no barcode: never constrained
    await _custom_food(db, a)


async def test_custom_food_client_id_unique_per_account(db, two_accounts):
    cid = "6d3a1c2e-0000-4000-8000-000000000001"
    await _custom_food(db, two_accounts.a, client_id=cid)
    with pytest.raises(IntegrityError) as exc_info:
        await _custom_food(db, two_accounts.a, client_id=cid)
    assert "uq_custom_foods_account_id_client_id" in str(exc_info.value)


@pytest.mark.parametrize(
    ("cols", "constraint"),
    [
        ({"name": ""}, "ck_custom_foods_name"),
        ({"name": "x" * 81}, "ck_custom_foods_name"),
        ({"basis": "kg"}, "ck_custom_foods_basis"),
        ({"serving_g": 0}, "ck_custom_foods_serving_g"),
        ({"density_g_per_ml": 0.19}, "ck_custom_foods_density"),
        ({"density_g_per_ml": 2.01}, "ck_custom_foods_density"),
    ],
)
async def test_custom_food_checks(db, two_accounts, cols, constraint):
    with pytest.raises(IntegrityError) as exc_info:
        await _custom_food(db, two_accounts.a, **cols)
    assert constraint in str(exc_info.value)


async def _recipe(db, account) -> object:
    async with db.begin_nested():
        return (
            await db.execute(
                text(
                    "insert into recipes (account_id, name, per_100g) "
                    "values (:a, 'Stew', '{}') returning id"
                ),
                {"a": account},
            )
        ).scalar_one()


async def _ingredient(db, account, recipe, position=0, **cols) -> None:
    values = {
        "recipe_id": recipe,
        "account_id": account,
        "position": position,
        "source_kind": "custom_food",
        "name": "x",
        "quantity": 1,
        "unit": "g",
        "grams": 10,
        "basis": "g",
        **cols,
    }
    names = ", ".join([*values, "per_100"])
    params = ", ".join(f":{k}" for k in values)
    async with db.begin_nested():
        await db.execute(
            text(f"insert into recipe_ingredients ({names}) values ({params}, '{{}}')"), values
        )


async def test_recipe_ingredient_ref_matches_kind(db, two_accounts):
    a = two_accounts.a
    recipe = await _recipe(db, a)
    food = await _food(db)
    cf = await _custom_food(db, a)
    p = two_accounts.product
    bad = (
        {"source_kind": "product"},  # product without a product id
        {"source_kind": "product", "product_id": p, "food_id": food},
        {"source_kind": "off"},  # off without a barcode
        {"source_kind": "food", "food_id": None},
        {"source_kind": "food", "food_id": food, "custom_food_id": cf},
        {"source_kind": "custom_food", "custom_food_id": cf, "food_id": food},
        {"source_kind": "custom_food", "off_barcode": "8901"},
        {"source_kind": "recipe"},  # not an ingredient kind
    )
    for i, cols in enumerate(bad):
        with pytest.raises(IntegrityError) as exc_info:
            await _ingredient(db, a, recipe, i, **cols)
        assert "ck_recipe_ingredients_" in str(exc_info.value), cols
    await _ingredient(db, a, recipe, 10, source_kind="product", product_id=p)
    await _ingredient(db, a, recipe, 11, source_kind="off", off_barcode="8901")
    await _ingredient(db, a, recipe, 12, source_kind="food", food_id=food)
    await _ingredient(db, a, recipe, 13, source_kind="custom_food", custom_food_id=cf)
    with pytest.raises(IntegrityError) as exc_info:  # one position per recipe
        await _ingredient(db, a, recipe, 13, source_kind="custom_food", custom_food_id=cf)
    assert "uq_recipe_ingredients_recipe_id_position" in str(exc_info.value)


async def test_custom_food_delete_sets_entry_and_ingredient_null(db, two_accounts):
    a = two_accounts.seed_a
    cf = await _custom_food(db, a.account)
    recipe = await _recipe(db, a.account)
    await _ingredient(db, a.account, recipe, 0, custom_food_id=cf)
    await _entry(db, a, None, source_kind="custom_food", custom_food_id=cf)
    await db.execute(text("delete from custom_foods where id = :c"), {"c": cf})
    ing = await db.scalar(
        text("select custom_food_id from recipe_ingredients where recipe_id = :r"), {"r": recipe}
    )
    assert ing is None
    row = (
        await db.execute(
            text(
                "select custom_food_id, source_kind from meal_logs "
                "where member_id = :m and source_kind = 'custom_food'"
            ),
            {"m": a.member},
        )
    ).one()
    assert tuple(row) == (None, "custom_food")  # the entry stays


async def test_meal_log_custom_food_null_allowed_after_delete(db, two_accounts):
    a = two_accounts.seed_a
    p = two_accounts.product
    # NULL ids are allowed for the two kinds (G21), but never mixed or for the other kinds.
    await _entry(db, a, None, source_kind="custom_food")
    await _entry(db, a, None, source_kind="recipe")
    cf = await _custom_food(db, a.account)
    recipe = await _recipe(db, a.account)
    bad = (
        {"source_kind": "recipe", "custom_food_id": cf},  # wrong column for the kind
        {"source_kind": "custom_food", "recipe_id": recipe},
        {"source_kind": "custom_food", "custom_food_id": cf, "recipe_id": recipe},
        {"source_kind": "custom_food", "grams": None},  # a portion is required
        {"source_kind": "custom_food", "product_id": p},
        {"source_kind": "product", "product_id": p, "custom_food_id": cf},
        {"source_kind": "quick_add", "grams": None, "recipe_id": recipe},
    )
    for cols in bad:
        values = {"product_id": None} | cols
        with pytest.raises(IntegrityError) as exc_info:
            await _entry(db, a, p, **values)
        assert "ck_meal_logs_ref" in str(exc_info.value), cols
    await _entry(db, a, None, source_kind="custom_food", custom_food_id=cf)
    await _entry(db, a, None, source_kind="recipe", recipe_id=recipe)


async def test_portion_custom_food_ref(db, two_accounts):
    a, b = two_accounts.a, two_accounts.b
    cf = await _custom_food(db, a)
    food = await _food(db)
    with pytest.raises(IntegrityError) as exc_info:  # two refs
        await _portion(db, custom_food_id=cf, food_id=food, account_id=a, source="user")
    assert "ck_food_portions_ref" in str(exc_info.value)
    await _portion(db, custom_food_id=cf, account_id=a, source="user", unit="piece")
    with pytest.raises(IntegrityError) as exc_info:
        await _portion(db, custom_food_id=cf, account_id=a, source="user", unit="piece")
    assert "uq_food_portions_custom_food" in str(exc_info.value)
    await _portion(db, custom_food_id=cf, account_id=b, source="user", unit="piece")
    await db.execute(text("delete from custom_foods where id = :c"), {"c": cf})
    n = await db.scalar(
        text("select count(*) from food_portions where custom_food_id = :c"), {"c": cf}
    )
    assert n == 0  # the portions go with the food (ON DELETE CASCADE)


# ---- Plan 12 slice 5 (migration 0012): favourites


async def _favourite(db, seed, **cols) -> object:
    values = {
        "account_id": seed.account,
        "member_id": seed.member,
        "kind": "food",
        "name": "Fav",
        **cols,
    }
    names = ", ".join(values)
    params = ", ".join(f":{k}" for k in values)
    async with db.begin_nested():
        return (
            await db.execute(
                text(f"insert into favourites ({names}) values ({params}) returning id"), values
            )
        ).scalar_one()


async def test_food_favourite_exactly_one_ref(db, two_accounts):
    a = two_accounts.seed_a
    cf = await _custom_food(db, a.account)
    food = await _food(db)
    bad = (
        {"source_kind": "custom_food"},  # no ref
        {"source_kind": "custom_food", "custom_food_id": cf, "food_id": food},  # two refs
        {"source_kind": "food", "custom_food_id": cf},  # ref does not match the kind
        {"source_kind": None, "custom_food_id": cf},  # a food needs its source kind
        {"source_kind": "mystery", "custom_food_id": cf},
        {"source_kind": "custom_food", "custom_food_id": cf, "items": "[]"},  # a food has no items
        {"source_kind": "custom_food", "custom_food_id": cf, "default_quantity": 1},  # no unit
        {
            "source_kind": "custom_food",
            "custom_food_id": cf,
            "default_quantity": 0,
            "default_unit": "g",
        },
    )
    for cols in bad:
        with pytest.raises(IntegrityError) as exc_info:
            await _favourite(db, a, **cols)
        assert "ck_favourites_" in str(exc_info.value), cols
    await _favourite(db, a, source_kind="custom_food", custom_food_id=cf)
    await _favourite(db, a, source_kind="food", food_id=food, default_quantity=2, default_unit="g")
    await _favourite(db, a, source_kind="off", off_barcode="8901")


async def test_meal_favourite_has_items_no_ref(db, two_accounts):
    a = two_accounts.seed_a
    cf = await _custom_food(db, a.account)
    bad = (
        {"kind": "meal"},  # no items
        {"kind": "meal", "items": '[{"a": 1}]', "custom_food_id": cf},  # a ref
        {"kind": "meal", "items": '[{"a": 1}]', "source_kind": "custom_food"},
        {"kind": "meal", "items": '[{"a": 1}]', "default_quantity": 1, "default_unit": "g"},
    )
    for cols in bad:
        with pytest.raises(IntegrityError) as exc_info:
            await _favourite(db, a, **cols)
        assert "ck_favourites_" in str(exc_info.value), cols
    await _favourite(db, a, kind="meal", items='[{"a": 1}]')
    await _favourite(db, a, kind="meal", items='[{"a": 1}]')  # meals are not unique


async def test_unique_food_favourite_per_member(db, two_accounts):
    a, b = two_accounts.seed_a, two_accounts.seed_b
    p = two_accounts.product
    await _favourite(db, a, source_kind="product", product_id=p)
    with pytest.raises(IntegrityError) as exc_info:
        await _favourite(db, a, source_kind="product", product_id=p)
    assert "uq_favourites_member_id_product_id" in str(exc_info.value)
    await _favourite(db, b, source_kind="product", product_id=p)  # another member: its own
    await _favourite(db, a, source_kind="off", off_barcode="8901")
    with pytest.raises(IntegrityError) as exc_info:
        await _favourite(db, a, source_kind="off", off_barcode="8901")
    assert "uq_favourites_member_id_off_barcode" in str(exc_info.value)


async def test_custom_food_delete_cascades_favourite(db, two_accounts):
    a = two_accounts.seed_a
    cf = await _custom_food(db, a.account)
    recipe = await _recipe(db, a.account)
    await _favourite(db, a, source_kind="custom_food", custom_food_id=cf)
    await _favourite(db, a, source_kind="recipe", recipe_id=recipe)
    await db.execute(text("delete from custom_foods where id = :c"), {"c": cf})
    await db.execute(text("delete from recipes where id = :r"), {"r": recipe})
    n = await db.scalar(
        text("select count(*) from favourites where custom_food_id = :c or recipe_id = :r"),
        {"c": cf, "r": recipe},
    )
    assert n == 0


async def test_favourite_client_id_unique_per_account(db, two_accounts):
    a = two_accounts.seed_a
    cid = uuid.uuid4()
    await _favourite(db, a, kind="meal", items='[{"a": 1}]', client_id=cid)
    with pytest.raises(IntegrityError) as exc_info:
        await _favourite(db, a, kind="meal", items='[{"a": 1}]', client_id=cid)
    assert "uq_favourites_account_id_client_id" in str(exc_info.value)


async def test_favourite_goes_with_its_member(db, two_accounts):
    a = two_accounts.seed_a
    await _favourite(db, a, kind="meal", items='[{"a": 1}]')
    await db.execute(text("delete from meal_logs where member_id = :m"), {"m": a.member})
    await db.execute(text("delete from meal_slots where member_id = :m"), {"m": a.member})
    await db.execute(text("delete from diary_days where member_id = :m"), {"m": a.member})
    await db.execute(text("delete from diary_goal_settings where member_id = :m"), {"m": a.member})
    await db.execute(text("delete from members where id = :m"), {"m": a.member})
    n = await db.scalar(
        text("select count(*) from favourites where member_id = :m"), {"m": a.member}
    )
    assert n == 0


@pytest.mark.parametrize("items", ["[]", "{}", "[" + ",".join(["{}"] * 51) + "]"])
async def test_favourite_meal_items_must_hold_1_to_50(db, two_accounts, items):
    member = await db.scalar(
        text("select id from members where account_id = :a limit 1"), {"a": two_accounts.a}
    )
    with pytest.raises(IntegrityError) as exc_info:
        await db.execute(
            text(
                "insert into favourites (account_id, member_id, kind, name, items) "
                "values (:a, :m, 'meal', 'M', cast(:items as jsonb))"
            ),
            {"a": two_accounts.a, "m": member, "items": items},
        )
    assert "ck_favourites" in str(exc_info.value)

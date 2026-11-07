"""The seed job: idempotent, stable ids, nothing written in check mode (Plan 12 Task 3)."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, text

from app.features.foods.models import Food, FoodPortion
from app.features.foods.seed import seed_foods
from app.jobs import seed_foods as job
from tests.api.foods.conftest import ACC_A

D = Decimal


async def _foods(db_session) -> dict[tuple[str, str], UUID]:
    rows = await db_session.execute(select(Food.source, Food.source_code, Food.id))
    return {(s, c): i for s, c, i in rows}


async def _count(db_session, model) -> int:
    return int(await db_session.scalar(select(func.count()).select_from(model)) or 0)


async def test_seed_writes_the_expected_rows(db_session):
    report = await seed_foods(db_session)
    assert (report.foods, report.dishes_seeded, report.portions, report.densities) == (
        141,
        21,
        19,
        20,
    )
    assert len(report.dishes_excluded) == 9
    assert await _count(db_session, Food) == 141 + 21
    assert await _count(db_session, FoodPortion) == 19
    foods = await _foods(db_session)
    dal = await db_session.get(Food, foods[("smartnutri_recipe", "dal_tadka")])
    assert dal.per_100["sugars_g"] is None and dal.per_100["sat_fat_g"] is None
    assert dal.per_100["energy_kcal"] > 0 and dal.serving_g is None
    assert dal.recipe["cooked_weight_g"] == 350 and dal.review_status == "pending_dietitian_review"
    egg = await db_session.get(Food, foods[("smartnutri_recipe", "egg_bhurji")])
    assert egg.serving_g == D("150")
    pigeon = await db_session.get(Food, foods[("usda_fdc", "172437")])
    assert pigeon.density_g_per_ml == D("0.71") and pigeon.density_source == "fdc_derived"
    assert pigeon.licence == "CC0 1.0" and "dal" in pigeon.aliases
    assert "toor dal" in pigeon.search_text and pigeon.search_text == pigeon.search_text.lower()
    papad = await db_session.get(Food, foods[("usda_fdc", "168106")])
    portions = await db_session.scalars(select(FoodPortion).where(FoodPortion.food_id == papad.id))
    assert list(portions) == []  # no piece weight in the CSV, so none is invented
    roti = await db_session.scalars(
        select(FoodPortion)
        .join(Food, Food.id == FoodPortion.food_id)
        .where(Food.source_code == "171844")
    )
    [row] = list(roti)
    assert (row.unit, row.grams_per_unit, row.source, row.account_id) == (
        "roti",
        D("68"),
        "reference_table",
        None,
    )


async def test_seed_is_idempotent(db_session):
    await seed_foods(db_session)
    first = await _foods(db_session)
    await seed_foods(db_session)
    assert await _foods(db_session) == first
    assert await _count(db_session, Food) == 162
    assert await _count(db_session, FoodPortion) == 19


async def test_reseed_keeps_food_ids_and_entries(db_session):
    await seed_foods(db_session)
    foods = await _foods(db_session)
    dal_id = foods[("smartnutri_recipe", "dal_tadka")]
    # A diary entry logged before the reseed.
    from app.core.security import AccountContext
    from app.features.me.service import ensure_account

    await ensure_account(db_session, AccountContext(ACC_A, None))
    member = (
        await db_session.execute(
            text(
                "insert into members (account_id, name, relation) values (:a, 'M', 'self') "
                "returning id"
            ),
            {"a": ACC_A},
        )
    ).scalar_one()
    slot = (
        await db_session.execute(
            text(
                "insert into meal_slots (account_id, member_id, position, label_key, is_default) "
                "values (:a, :m, 0, 'diary.slot.breakfast', true) returning id"
            ),
            {"a": ACC_A, "m": member},
        )
    ).scalar_one()
    snapshot = '{"name": "Dal tadka (toor)", "per_100": {"energy_kcal": 79.69}}'
    entry = (
        await db_session.execute(
            text(
                "insert into meal_logs (account_id, member_id, source_kind, food_id, grams, "
                "quantity, unit, nutrients, food_snapshot, local_date, meal_slot_id) values "
                "(:a, :m, 'food', :f, 142, 1, 'g', '{}', cast(:s as jsonb), current_date, :slot) "
                "returning id"
            ),
            {"a": ACC_A, "m": member, "f": dal_id, "s": snapshot, "slot": slot},
        )
    ).scalar_one()
    await seed_foods(db_session)
    assert (await _foods(db_session))[("smartnutri_recipe", "dal_tadka")] == dal_id
    row = (
        await db_session.execute(
            text("select food_id, food_snapshot from meal_logs where id = :i"), {"i": entry}
        )
    ).one()
    assert row.food_id == dal_id and row.food_snapshot["per_100"]["energy_kcal"] == 79.69


async def test_reseed_restores_edited_reference_values_but_not_user_overrides(db_session, accounts):
    from tests.api.foods.conftest import portion

    await seed_foods(db_session)
    foods = await _foods(db_session)
    pigeon = await db_session.get(Food, foods[("usda_fdc", "172437")])
    pigeon.name_en = "tampered"
    db_session.add(portion(pigeon.id, "piece", 7, account_id=ACC_A))
    await db_session.flush()
    await seed_foods(db_session)
    await db_session.refresh(pigeon)
    assert pigeon.name_en.startswith("Pigeon peas")
    user = await db_session.scalars(
        select(FoodPortion).where(FoodPortion.account_id == ACC_A, FoodPortion.unit == "piece")
    )
    assert [p.grams_per_unit for p in user] == [D("7")]


async def test_check_mode_writes_nothing(db_session, capsys):
    report = await seed_foods(db_session, dry_run=True)
    assert await _count(db_session, Food) == 0 and await _count(db_session, FoodPortion) == 0
    assert (report.foods, report.dishes_seeded, report.portions, report.densities) == (
        141,
        21,
        19,
        20,
    )
    assert job.main(["--check"]) == 0  # no database is touched
    out = capsys.readouterr().out
    assert "141 foods" in out and "21 dishes seeded" in out and "9 dishes excluded" in out
    assert "poha: blocked" in out and "idli: needs_weighing" in out
    assert "19 portions" in out and "20 densities" in out
    assert await _count(db_session, Food) == 0


async def test_reseed_retires_a_dish_that_left_the_seeded_set(db_session):
    from app.features.foods.schemas import SearchKind
    from app.features.foods.service import search_foods

    await seed_foods(db_session)
    ghost = Food(
        source="smartnutri_recipe",
        source_code="ghost_dish",
        name_en="Ghost khichdi zzq",
        search_text="ghost khichdi zzq",
        basis="g",
        per_100={},
        licence="x",
        data_version="x",
    )
    db_session.add(ghost)
    await db_session.flush()

    async def hits() -> list[str]:
        out = await search_foods(
            db_session, None, "zzq", 20, {SearchKind.FOOD}, account_id=ACC_A, settings=None
        )
        return [h.name for h in out.items]

    assert await hits() == ["Ghost khichdi zzq"]
    await seed_foods(db_session)
    await db_session.refresh(ghost)
    assert ghost.review_status == "retired"
    assert await hits() == []
    await seed_foods(db_session)  # idempotent
    await db_session.refresh(ghost)
    assert ghost.review_status == "retired"
    assert await _count(db_session, Food) == 163
    # A seeded dish is never retired, and one that returns is listed again.
    foods = await _foods(db_session)
    dal = await db_session.get(Food, foods[("smartnutri_recipe", "dal_tadka")])
    assert dal.review_status == "pending_dietitian_review"
    dal.review_status = "retired"
    await db_session.flush()
    await seed_foods(db_session)
    await db_session.refresh(dal)
    assert dal.review_status == "pending_dietitian_review"

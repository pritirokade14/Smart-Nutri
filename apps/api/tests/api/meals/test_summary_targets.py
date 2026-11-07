"""Plan 10 Task 5: `meals_summary` takes its protein target from the daily targets engine when
the member has goal settings and `health_data` is active (Ruling D10), and redacts the numbers
the user chose to hide (Ruling D11), whether or not consent is active."""

from uuid import UUID

import pytest
from sqlalchemy import select, update

from app.core.time import today_ist
from app.features.members.models import Member
from app.features.targets.models import DiaryGoalSettings
from tests.api.meals.conftest import ACC_A
from tests.api.members.conftest import grant  # noqa: F401  (shared fixture)

pytestmark = pytest.mark.usefixtures("family")


@pytest.fixture
async def g11(db_session, family, grant) -> UUID:  # noqa: F811
    """The primary: male, 175 cm, 70 kg, build_muscle, body fat 15 % (G11), with settings and
    all consents granted."""
    await grant(ACC_A)
    me = await db_session.get(Member, family.me)
    me.birth_year = today_ist().year - 29
    me.sex, me.height_cm, me.weight_kg = "male", 175, 70
    me.goal, me.body_fat_pct = "build_muscle", 15
    db_session.add(
        DiaryGoalSettings(
            member_id=me.id,
            account_id=ACC_A,
            direction="gain",
            activity_level="moderate",
            rate_pct_bw_per_week=0.25,
        )
    )
    await db_session.flush()
    return me.id


async def _summary(client, member, period="day"):
    r = await client.get(f"/v1/meals/summary?member_id={member}&period={period}")
    assert r.status_code == 200, r.text
    return r.json()


async def _log(client, member, product, **kw):
    r = await client.post(
        "/v1/meals", json={"member_id": str(member), "product_id": str(product), **kw}
    )
    assert r.status_code == 201, r.text


async def _set(db_session, member, **values):
    await db_session.execute(
        update(DiaryGoalSettings).where(DiaryGoalSettings.member_id == member).values(**values)
    )
    await db_session.flush()


async def test_summary_protein_from_targets(client, g11):
    s = await _summary(client, g11)
    assert s["limits"]["protein_target_g"] == 119.0
    assert s["limits"]["protein_basis"] == "lean_mass"
    assert s["limits"]["protein_g_per_kg"] == 2.0
    assert s["limits"]["protein_target_status"] == "ready"
    assert s["protein_left_g"] == 119.0
    assert s["numbers_hidden"] == {"energy": False, "macros": False}
    week = await _summary(client, g11, "week")
    assert week["limits"]["protein_target_g"] == 119.0


async def test_summary_protein_left_uses_the_engine_target(client, g11, sf_biscuit_product_id):
    await _log(client, g11, sf_biscuit_product_id, grams=500)  # 40 g protein
    s = await _summary(client, g11)
    assert s["totals"]["protein_g"] == 40.0 and s["protein_left_g"] == 79.0


async def test_summary_legacy_without_settings(client, family, db_session, grant):  # noqa: F811
    await grant(ACC_A)
    dad = await db_session.get(Member, family.dad)
    dad.goal, dad.weight_kg = "weight_loss", 70
    await db_session.flush()
    s = await _summary(client, family.dad)
    assert s["limits"]["protein_target_g"] == 84.0  # 70 x 1.2 (Q8), the legacy rule
    assert s["limits"]["protein_basis"] == "actual_weight"
    assert s["limits"]["protein_target_status"] is None
    assert s["numbers_hidden"] == {"energy": False, "macros": False}


async def test_summary_legacy_without_a_target_has_no_basis(client, family, grant):  # noqa: F811
    await grant(ACC_A)
    s = await _summary(client, family.riya)  # 9 years old, no weight
    assert s["limits"]["protein_target_g"] is None
    assert s["limits"]["protein_basis"] is None and s["limits"]["protein_target_status"] is None


async def test_summary_legacy_without_health_data(client, g11, db_session, grant):  # noqa: F811
    from sqlalchemy import delete

    from app.features.consents.models import Consent

    await db_session.execute(
        delete(Consent).where(Consent.account_id == ACC_A, Consent.purpose == "health_data")
    )
    await db_session.flush()
    s = await _summary(client, g11)
    # Settings exist but health_data is not active: the legacy weight x g/kg rule applies.
    assert s["limits"]["protein_target_g"] == 112.0  # 70 x 1.6, not the lean-mass 119
    assert s["limits"]["protein_basis"] == "actual_weight"
    assert s["limits"]["protein_target_status"] is None


async def test_summary_pregnancy_has_no_protein_target(client, g11, db_session):
    await _set(db_session, g11, pregnant_or_breastfeeding=True)
    s = await _summary(client, g11)
    assert s["limits"]["protein_target_g"] is None and s["limits"]["protein_g_per_kg"] is None
    assert s["limits"]["protein_target_status"] == "paused_pregnancy"
    assert s["limits"]["protein_basis"] is None
    assert s["protein_left_g"] is None
    assert s["bands"]["protein_g"] == "unknown"


@pytest.mark.parametrize(
    ("change", "status"),
    [({"birth_year": 2015}, "not_available_minor"), ({"height_cm": None}, "needs_body_data")],
)
async def test_summary_non_ready_statuses(client, g11, db_session, change, status):
    me = await db_session.get(Member, g11)
    for key, value in change.items():
        setattr(me, key, value)
    await db_session.flush()
    s = await _summary(client, g11)
    assert s["limits"]["protein_target_g"] is None
    assert s["limits"]["protein_target_status"] == status


async def test_summary_hide_energy(client, g11, sf_biscuit_product_id):
    await _log(client, g11, sf_biscuit_product_id, grams=100)
    shown = await _summary(client, g11, "week")
    await _set_display(client, "hide_energy")
    s = await _summary(client, g11, "week")
    assert s["totals"]["energy_kcal"] is None
    assert all(d["totals"]["energy_kcal"] is None for d in s["days"])
    assert s["totals"]["sugars_g"] == shown["totals"]["sugars_g"] is not None
    assert s["totals"]["protein_g"] == shown["totals"]["protein_g"]
    assert s["limits"]["protein_target_g"] == 119.0
    assert s["numbers_hidden"] == {"energy": True, "macros": False}
    assert s["bands"] == shown["bands"] and s["incomplete"] == shown["incomplete"]


async def _set_display(client, value):
    r = await client.put("/v1/targets/display", json={"numbers_display": value})
    assert r.status_code == 200, r.text


async def test_summary_hide_all(client, g11, sf_biscuit_product_id):
    await _log(client, g11, sf_biscuit_product_id, grams=100)
    shown = await _summary(client, g11)
    assert shown["totals"]["sugars_g"] is not None and shown["protein_left_g"] is not None
    await _set_display(client, "hide_all")
    s = await _summary(client, g11)
    assert all(v is None for v in s["totals"].values())
    for day in s["days"]:
        assert all(v is None for v in day["totals"].values())
    assert s["limits"]["protein_target_g"] is None and s["protein_left_g"] is None
    assert s["limits"]["protein_g_per_kg"] is None
    assert s["numbers_hidden"] == {"energy": True, "macros": True}
    assert s["bands"] == shown["bands"]  # bands stay
    assert s["incomplete"] == shown["incomplete"]
    assert s["limits"]["sugar_g"] == shown["limits"]["sugar_g"]  # limits are not totals
    assert s["limits"]["protein_basis"] == "lean_mass"


async def test_hidden_numbers_apply_without_health_data(client, g11, db_session):
    from sqlalchemy import delete

    from app.features.consents.models import Consent

    await _set(db_session, g11, numbers_display="hide_all")
    await db_session.execute(
        delete(Consent).where(Consent.account_id == ACC_A, Consent.purpose == "health_data")
    )
    await db_session.flush()
    s = await _summary(client, g11)
    assert s["numbers_hidden"] == {"energy": True, "macros": True}  # hiding is less processing
    assert s["limits"]["protein_target_g"] is None and s["protein_left_g"] is None
    assert s["limits"]["protein_target_status"] is None  # legacy rule, then hidden


async def test_summary_other_member_unaffected(client, g11, family, db_session):
    await _set(db_session, g11, numbers_display="hide_all")
    dad = await db_session.get(Member, family.dad)
    s = await _summary(client, family.dad)
    assert s["numbers_hidden"] == {"energy": False, "macros": False}
    assert s["limits"]["protein_target_g"] == 58.1 and dad.goal is None
    assert s["limits"]["protein_target_status"] is None


async def test_settings_rows_are_not_created_by_reading(client, g11, db_session):
    await _summary(client, g11)
    rows = (await db_session.scalars(select(DiaryGoalSettings))).all()
    assert len(rows) == 1


async def test_fallback_uses_adjusted_weight(client, family, db_session, grant):  # noqa: F811
    """No goal settings, BMI 40: the adjusted body weight (Devine, 0.25), not the actual 116 kg
    x 1.2 = 139 g. Same reference weight and caps as `targets.compute`."""
    await grant(ACC_A)
    dad = await db_session.get(Member, family.dad)
    dad.goal, dad.weight_kg, dad.height_cm, dad.sex = "weight_loss", 116, 170, "male"
    dad.body_fat_pct = None
    await db_session.flush()
    s = await _summary(client, family.dad)
    assert s["limits"]["protein_basis"] == "adjusted_weight"
    assert s["limits"]["protein_target_g"] == pytest.approx(94.1, abs=0.1)
    assert s["limits"]["protein_g_per_kg"] == 1.2
    assert s["limits"]["protein_target_status"] is None


async def test_fallback_uses_lean_mass(client, family, db_session, grant):  # noqa: F811
    await grant(ACC_A)
    dad = await db_session.get(Member, family.dad)
    dad.goal, dad.weight_kg, dad.height_cm, dad.sex = "build_muscle", 80, 180, "male"
    dad.body_fat_pct = 20
    await db_session.flush()
    s = await _summary(client, family.dad)
    assert s["limits"]["protein_basis"] == "lean_mass"
    assert s["limits"]["protein_target_g"] == pytest.approx(128.0, abs=0.1)  # 80 x 0.8 x 2.0


async def test_summary_protein_from_frozen_day(client, g11, db_session):
    """Plan 11 Ruling E15: a past day uses that day's frozen row, not today's live settings."""
    from datetime import date

    from sqlalchemy.dialects.postgresql import insert

    from app.features.diary.frozen import to_row_values
    from app.features.diary.models import DiaryDay
    from app.features.targets import service as targets_service
    from app.scoring import targets as engine

    me = await db_session.get(Member, g11)
    day = date.fromisoformat("2026-11-05")
    row = await targets_service.get_settings(db_session, me)
    result = engine.compute(targets_service.body_data(me, day), targets_service.goal_settings(row))
    await db_session.execute(
        insert(DiaryDay).values(
            member_id=me.id, local_date=day, account_id=ACC_A, **to_row_values(result)
        )
    )
    await _set(db_session, g11, direction="lose", rate_pct_bw_per_week=0.5)  # today moves on
    r = await client.get(f"/v1/meals/summary?member_id={g11}&period=day&date=2026-11-05")
    s = r.json()
    assert s["limits"]["protein_target_g"] == 119.0
    assert s["limits"]["protein_target_status"] == "ready"
    assert s["limits"]["protein_basis"] == "lean_mass"


async def test_summary_past_day_without_row_is_legacy(client, g11):
    r = await client.get(f"/v1/meals/summary?member_id={g11}&period=day&date=2026-11-05")
    s = r.json()
    assert s["limits"]["protein_target_status"] is None  # the legacy rule, no frozen day
    assert s["limits"]["protein_target_g"] is not None

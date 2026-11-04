"""Plan 9 Task 6: `protein_left_g` on the day summary (a guide, never a need).

period=day only: max(0, limits.protein_target_g - totals.protein_g), 1 dp. Null without a
target, when protein is incomplete for the day, and for period=week. Nothing logged yet:
the whole target is left (nothing has been counted).
"""

from uuid import UUID

import pytest

from app.core.time import today_ist
from app.features.members.models import Member
from tests.api.meals.conftest import ACC_A, OFF_BARCODE, OFF_PAYLOAD, FakeOff

pytestmark = pytest.mark.usefixtures("family")


@pytest.fixture
async def gym_member(db_session) -> UUID:
    """An adult (26), 70 kg, goal build_muscle: target 70 x 1.6 = 112 g."""
    member = Member(
        account_id=ACC_A,
        name="Arjun",
        relation="other",
        birth_year=today_ist().year - 27,
        diet="non_veg",
        allergens=[],
        conditions=[],
        goal="build_muscle",
        weight_kg=70,
    )
    db_session.add(member)
    await db_session.flush()
    return member.id


async def _log(client, member, product=None, **kw):
    body = {"member_id": str(member), **kw}
    if product is not None:
        body["product_id"] = str(product)
    r = await client.post("/v1/meals", json=body)
    assert r.status_code == 201, r.text


async def _summary(client, member, period="day"):
    r = await client.get(f"/v1/meals/summary?member_id={member}&period={period}")
    assert r.status_code == 200, r.text
    return r.json()


async def test_protein_left_day(client, gym_member, sf_biscuit_product_id):
    # sf_biscuit: 8 g protein per 100 g; 500 g -> 40 g eaten.
    await _log(client, gym_member, sf_biscuit_product_id, grams=500)
    s = await _summary(client, gym_member)
    assert s["limits"]["protein_target_g"] == 112.0
    assert s["totals"]["protein_g"] == 40.0
    assert s["protein_left_g"] == 72.0


async def test_protein_left_never_negative(client, gym_member, sf_biscuit_product_id):
    await _log(client, gym_member, sf_biscuit_product_id, grams=1500)  # 120 g
    s = await _summary(client, gym_member)
    assert s["totals"]["protein_g"] == 120.0 and s["protein_left_g"] == 0.0
    assert s["bands"]["protein_g"] == "ok"


async def test_protein_left_nothing_logged_is_the_target(client, gym_member):
    s = await _summary(client, gym_member)
    assert s["totals"]["protein_g"] is None and s["protein_left_g"] == 112.0


async def test_protein_left_null_without_target_or_incomplete(
    client, family, gym_member, sf_biscuit_product_id, login
):
    # Riya (9, no weight): no protein target.
    await _log(client, family.riya, sf_biscuit_product_id, grams=100)
    s = await _summary(client, family.riya)
    assert s["limits"]["protein_target_g"] is None and s["protein_left_g"] is None

    # An Open Food Facts product with no protein value makes the day incomplete.
    no_protein = {
        **OFF_PAYLOAD,
        "nutriments": {k: v for k, v in OFF_PAYLOAD["nutriments"].items() if k != "proteins_100g"},
    }
    login(ACC_A, off=FakeOff(no_protein))
    await _log(client, gym_member, sf_biscuit_product_id, grams=100)
    await _log(client, gym_member, barcode=OFF_BARCODE, grams=30)
    s = await _summary(client, gym_member)
    assert s["incomplete"]["protein_g"] is True and s["totals"]["protein_g"] == 8.0
    assert s["protein_left_g"] is None


async def test_protein_left_null_for_week(client, gym_member, sf_biscuit_product_id):
    await _log(client, gym_member, sf_biscuit_product_id, grams=500)
    s = await _summary(client, gym_member, period="week")
    assert s["limits"]["protein_target_g"] == 112.0 and s["protein_left_g"] is None


async def test_protein_left_for_the_default_goal(client, family, sf_biscuit_product_id):
    # Dad (61, 70 kg, no goal): 58.1 g target; 16 g eaten -> 42.1 g left.
    await _log(client, family.dad, sf_biscuit_product_id, grams=200)
    s = await _summary(client, family.dad)
    assert s["protein_left_g"] == 42.1


async def test_summary_exposes_protein_per_kg(client, family, gym_member):
    # The YAML g/kg the target was computed with (the protein.guide copy); null with no target.
    s = await _summary(client, gym_member)
    assert s["limits"]["protein_g_per_kg"] == 1.6
    week = await _summary(client, gym_member, period="week")
    assert week["limits"]["protein_g_per_kg"] == 1.6
    assert (await _summary(client, family.dad))["limits"]["protein_g_per_kg"] == 0.83
    riya = await _summary(client, family.riya)
    assert riya["limits"]["protein_target_g"] is None
    assert riya["limits"]["protein_g_per_kg"] is None

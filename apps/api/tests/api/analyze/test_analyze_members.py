"""POST /v1/analyze with the account's family (Plan 5 Task 6; rulings P2, P8.2).

- No `member_ids`: every member of the account, the primary first (created if missing).
- Explicit `member_ids`: only the account's own; any unknown or foreign id is a 404
  `member_not_found` (Review Focus 5 wins over the plan's "silently ignore").
- Verdicts carry display-only `relation` and `is_primary`; there is no `top_reason`
  (clients use `reasons[0]`, which the engine ranks most severe first).
"""

import unicodedata
from datetime import date
from uuid import uuid4

from sqlalchemy import func, select

from app.features.analyze import router as analyze_router
from app.features.members.models import Member
from app.features.products.models import Product
from app.features.scans.models import Scan
from tests.api.analyze.conftest import A, today

URL = "/v1/analyze"
MEMBERS = "/v1/members"


async def _analyze(client, product, member_ids=None, **extra):
    body = {"product_id": str(product.id), **extra}
    if member_ids is not None:
        body["member_ids"] = [str(m) for m in member_ids]
    return await client.post(URL, json=body)


async def _scan_count(db_session) -> int:
    return await db_session.scalar(select(func.count()).select_from(Scan))


# --- whole family by default -----------------------------------------------------------------


async def test_family_verdicts_on_biscuit(auth_client, seeded_family, sf_biscuit_product):
    r = await _analyze(auth_client, sf_biscuit_product, language="en")
    assert r.status_code == 200, r.text
    verdicts = r.json()["verdicts"]
    by_name = {v["member_name"]: v["status"] for v in verdicts}
    # diabetic parent, milk-allergic child, weight-loss account holder
    assert by_name == {"Dad": "avoid", "Riya": "avoid", "Me": "caution"}
    assert [v["member_name"] for v in verdicts] == ["Me", "Dad", "Riya"]  # primary first


async def test_verdicts_carry_relation_and_is_primary(
    auth_client, seeded_family, sf_biscuit_product
):
    verdicts = (await _analyze(auth_client, sf_biscuit_product)).json()["verdicts"]
    assert [(v["relation"], v["is_primary"]) for v in verdicts] == [
        ("self", True),
        ("parent", False),
        ("child", False),
    ]
    assert [v["member_id"] for v in verdicts] == [
        str(seeded_family[n].id) for n in ("Me", "Dad", "Riya")
    ]
    for v in verdicts:
        assert "top_reason" not in v


async def test_reasons_are_most_severe_first(auth_client, seeded_family, sf_biscuit_product):
    verdicts = (await _analyze(auth_client, sf_biscuit_product)).json()["verdicts"]
    rank = {"ok": 0, "caution": 1, "unknown": 2, "avoid": 3}
    for v in verdicts:
        severities = [rank[x["severity"]] for x in v["reasons"]]
        assert severities == sorted(severities, reverse=True)
        assert rank[v["reasons"][0]["severity"]] == rank[v["status"]]


async def test_no_member_ids_creates_primary_and_includes_everyone(
    auth_client, own_member, sf_biscuit_product, count_members
):
    """An account whose only row is a non-primary member still gets its primary, first."""
    r = await _analyze(auth_client, sf_biscuit_product)
    assert r.status_code == 200
    verdicts = r.json()["verdicts"]
    assert len(verdicts) == 2 and await count_members(A) == 2
    assert verdicts[0]["is_primary"] is True and verdicts[0]["relation"] == "self"
    assert verdicts[1]["member_id"] == str(own_member.id)


async def test_explicit_member_ids_select_a_subset(auth_client, seeded_family, sf_biscuit_product):
    riya = seeded_family["Riya"]
    r = await _analyze(auth_client, sf_biscuit_product, [riya.id])
    (v,) = r.json()["verdicts"]
    assert v["member_name"] == "Riya" and v["status"] == "avoid"
    assert v["relation"] == "child" and v["is_primary"] is False


async def test_claims_in_report(auth_client, seeded_family, sf_biscuit_product):
    claims = (await _analyze(auth_client, sf_biscuit_product)).json()["report"]["claims"]
    assert claims[0]["claim"] == "sugar_free" and claims[0]["verdict"] == "contradicted"


# --- member data reaches the engine ----------------------------------------------------------


async def test_other_allergen_reaches_engine(auth_client, db_session, grant):
    """Free-text allergens typed into the members API (Latin and Devanagari) give `avoid`."""
    await grant(A, ["health_data"])
    product = Product(
        name="Kiwi yogurt",
        source="label",
        verification_status="verified",
        category="general",
        per_100g={"sugars_g": 3.0, "salt_g": 0.1, "energy_kcal": 90},
        ingredients_text="Yogurt base, kiwi pulp (10%), किवी गूदा, pectin",
        claims=[],
    )
    db_session.add(product)
    await db_session.flush()
    devanagari_nfd = unicodedata.normalize("NFD", "किवी")
    ids = []
    for allergen in ("Kiwi", devanagari_nfd):
        created = await auth_client.post(
            MEMBERS,
            json={"name": "Kid", "relation": "child", "birth_year": 2016, "allergens": [allergen]},
        )
        assert created.status_code == 201, created.text
        ids.append(created.json()["id"])
    r = await _analyze(auth_client, product, ids)
    assert r.status_code == 200
    for v in r.json()["verdicts"]:
        assert v["status"] == "avoid"
        assert v["reasons"][0]["code"] == "allergen_contains"
        assert v["reasons"][0]["severity"] == "avoid"


async def test_custom_alerts_reach_engine(auth_client, db_session, sf_biscuit_product):
    member = Member(
        account_id=A,
        name="Asha",
        relation="spouse",
        birth_year=1990,
        diet="non_veg",
        custom_alerts=["palm_oil", "maida"],
    )
    await auth_client.post(URL, json={"product_id": str(sf_biscuit_product.id)})  # account row
    db_session.add(member)
    await db_session.flush()
    (v,) = (await _analyze(auth_client, sf_biscuit_product, [member.id])).json()["verdicts"]
    alerts = [x["params"]["alert"] for x in v["reasons"] if x["code"] == "custom_alert"]
    assert alerts == ["palm_oil", "maida"]


async def test_birth_year_this_year_is_infant(auth_client, db_session, grant, cola_product):
    await grant(A, ["health_data"])
    created = await auth_client.post(
        MEMBERS, json={"name": "Baby", "relation": "child", "birth_year": today().year}
    )
    assert created.status_code == 201, created.text
    r = await _analyze(auth_client, cola_product, [created.json()["id"]])
    (v,) = r.json()["verdicts"]
    assert v["status"] == "avoid"
    assert "infant_added_sugar" in {x["code"] for x in v["reasons"]}


async def test_analyze_uses_ist_today(auth_client, db_session, cola_product, monkeypatch):
    """The router's "today" is app.core.time.today_ist (Ruling P8.2)."""
    member = Member(account_id=A, name="Kid", relation="child", birth_year=2020, diet="non_veg")
    await auth_client.post(URL, json={"product_id": str(cola_product.id)})  # account row
    db_session.add(member)
    await db_session.flush()
    monkeypatch.setattr(analyze_router, "today_ist", lambda: date(2021, 6, 1))
    (v,) = (await _analyze(auth_client, cola_product, [member.id])).json()["verdicts"]
    assert any(x["code"].startswith("infant_") for x in v["reasons"])  # age 0 in 2021


# --- ownership (Review Focus 5) --------------------------------------------------------------


async def test_analyze_foreign_member_ids_is_404(
    auth_client, db_session, seeded_family, other_account_member, sf_biscuit_product
):
    before = await _scan_count(db_session)
    for ids in (
        [other_account_member.id],
        [seeded_family["Me"].id, other_account_member.id],
        [uuid4()],
    ):
        r = await _analyze(auth_client, sf_biscuit_product, ids)
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "member_not_found"
        assert "Other" not in r.text
    assert await _scan_count(db_session) == before

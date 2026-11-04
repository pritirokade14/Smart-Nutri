from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.time import today_ist
from app.features.scans.models import Scan
from tests.api.meals.conftest import ACC_A, ACC_C, OFF_BARCODE

pytestmark = pytest.mark.usefixtures("family")


async def _log(client, member, product=None, **kw):
    body = {"member_id": str(member), **kw}
    if product is not None:
        body["product_id"] = str(product)
    r = await client.post("/v1/meals", json=body)
    assert r.status_code == 201, r.text
    return r.json()


# --- plan test ----------------------------------------------------------------------------


async def test_summary_endpoint_for_diabetic_parent(client, family, sf_biscuit_product_id):
    for _ in range(2):
        await _log(client, family.dad, sf_biscuit_product_id, servings=1)
    r = await client.get(f"/v1/meals/summary?member_id={family.dad}&period=day")
    assert r.status_code == 200
    s = r.json()
    assert s["totals"]["sugars_g"] == 1.0 and s["limits"]["sugar_g"] == 25
    # 70 kg x 0.83 g/kg, from the members row (an adult: Ruling M1 S3)
    assert s["limits"]["protein_target_g"] == 58.1
    # Far below the protein target: no band (Ruling M1 S2).
    assert s["bands"]["protein_g"] == "unknown"
    assert (s["period"], s["start"], s["end"]) == ("day", str(today_ist()), str(today_ist()))
    assert s["bands"]["sugar_g"] == "ok" and s["incomplete"]["sugars_g"] is False
    assert s["pending_clinician_review"] is True


# --- more ---------------------------------------------------------------------------------


async def test_off_product_without_sugars_is_incomplete(client, family, sf_biscuit_product_id):
    await _log(client, family.dad, sf_biscuit_product_id, servings=1)
    await _log(client, family.dad, barcode=OFF_BARCODE, grams=30)
    s = (await client.get(f"/v1/meals/summary?member_id={family.dad}")).json()
    assert s["totals"]["sugars_g"] == 0.5  # the known meal only
    assert s["incomplete"]["sugars_g"] is True and s["bands"]["sugar_g"] == "unknown"
    assert s["incomplete"]["energy_kcal"] is False


async def test_week_summary_for_child(client, family, sf_biscuit_product_id):
    await _log(client, family.riya, sf_biscuit_product_id, grams=100)
    s = (await client.get(f"/v1/meals/summary?member_id={family.riya}&period=week")).json()
    assert len(s["days"]) == 7 and s["days"][-1]["date"] == str(today_ist())
    assert s["start"] == str(today_ist() - timedelta(days=6))
    # Age 8: NHS child bands (sugar 24 g, salt 5 g); no weight -> no protein target.
    assert s["limits"] == {
        "sugar_g": 24,
        "salt_g": 5,
        "protein_target_g": None,
        "kcal": None,
        "protein_g_per_kg": None,
    }
    assert s["days"][-1]["items"] == 1 and s["days"][0]["items"] == 0
    assert s["days"][0]["bands"]["sugar_g"] == "unknown"
    # Ruling M1 S1: an empty day has null totals, never 0.0.
    assert s["days"][0]["totals"] == {
        "energy_kcal": None,
        "sugars_g": None,
        "salt_g": None,
        "protein_g": None,
    }


async def test_summary_for_a_past_date(client, family, sf_biscuit_product_id):
    yesterday = today_ist() - timedelta(days=1)
    s = (
        await client.get(
            "/v1/meals/summary",
            params={"member_id": str(family.me), "period": "day", "date": str(yesterday)},
        )
    ).json()
    assert s["end"] == str(yesterday) and s["days"][0]["items"] == 0
    assert set(s["totals"].values()) == {None}


async def test_summary_foreign_member_404(client, family, other_account_member_id):
    r = await client.get(f"/v1/meals/summary?member_id={other_account_member_id}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"


async def test_summary_bad_period_422(client, family):
    r = await client.get(f"/v1/meals/summary?member_id={family.me}&period=month")
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_week_counts(client, family, sf_biscuit_product_id, db_session, login):
    await _log(client, family.me, sf_biscuit_product_id, grams=10)
    await _log(client, family.dad, sf_biscuit_product_id, grams=10)
    # Two analyses and one label scan (a photo, not a check) for ACC_A; one for ACC_C.
    db_session.add_all(
        [
            Scan(id=uuid4(), account_id=ACC_A, analysis={"report": {}, "verdicts": []}),
            Scan(id=uuid4(), account_id=ACC_A, analysis={"report": {}, "verdicts": []}),
            Scan(id=uuid4(), account_id=ACC_A, image_path=f"{ACC_A}/x.jpg", analysis={"draft": {}}),
        ]
    )
    from app.core.security import AccountContext
    from app.features.me.service import ensure_account

    await ensure_account(db_session, AccountContext(ACC_C, None))
    db_session.add(Scan(id=uuid4(), account_id=ACC_C, analysis={"report": {}, "verdicts": []}))
    await db_session.flush()
    r = await client.get("/v1/meals/week_counts")
    assert r.status_code == 200
    assert r.json() == {
        "start": str(today_ist() - timedelta(days=6)),
        "end": str(today_ist()),
        "scans": 2,
        "logged": 2,
    }

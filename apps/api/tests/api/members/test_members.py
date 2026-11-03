"""Members CRUD with the health-data consent gate (Plan 5 Task 5; rulings P2, P5, P5-R6/R7/R12).

The gate: writing a non-empty allergens, conditions, goal, height_cm or weight_kg needs an
active `health_data` consent at the current version. Only the fields being written are checked.
`ai_processing` never gates a member save.
"""

import typing
import unicodedata
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import select, text

from app import scoring
from app.core.time import today_ist
from app.features.members.models import Member
from app.features.members.schemas import CANONICAL_ALLERGENS, CustomAlert
from app.features.members.service import list_members, youngest_age
from tests.api.members.conftest import ACC_A, ACC_B

URL = "/v1/members"
KID = {"name": "Riya", "relation": "child", "birth_year": 2018}


def _err(r) -> dict:
    return r.json()["error"]


async def _row(db_session, member_id) -> Member:
    return await db_session.scalar(
        select(Member).where(Member.id == member_id).execution_options(populate_existing=True)
    )


# --- pure helpers ---------------------------------------------------------------------------


def test_youngest_age():
    assert youngest_age(2026, date(2026, 11, 3)) == 0
    assert youngest_age(None, date(2026, 11, 3)) is None
    assert youngest_age(2016, date(2026, 11, 3)) == 9  # birthday may still be ahead
    assert youngest_age(2027, date(2026, 11, 3)) is None


def test_custom_alert_keys_come_from_the_engine():
    assert typing.get_args(CustomAlert) == scoring.CUSTOM_ALERT_KEYS


def test_canonical_allergens_match_engine_data():
    assert set(CANONICAL_ALLERGENS) == set(scoring.load_config().allergens)


# --- list and primary -------------------------------------------------------------------------


async def test_list_ensures_primary_first(client, login, count_members):
    login(ACC_B)
    r = await client.get(URL)
    assert r.status_code == 200
    [me] = r.json()
    assert me["is_primary"] is True and me["relation"] == "self" and me["birth_year"] is None
    assert "age" not in me
    assert await count_members(ACC_B) == 1
    await client.get(URL)
    assert await count_members(ACC_B) == 1  # idempotent


async def test_create_list_primary(client, consented):
    r = await client.post(URL, json=KID)
    assert r.status_code == 201
    body = r.json()
    assert body["is_primary"] is False and body["relation"] == "child"
    assert body["diet"] == "non_veg" and body["allergens"] == [] and body["goal"] is None
    listed = (await client.get(URL)).json()
    assert [m["is_primary"] for m in listed] == [True, False]
    assert listed[1]["id"] == body["id"]


async def test_list_order_is_primary_then_creation(client, consented):
    names = ["B", "A", "C"]
    for n in names:
        assert (await client.post(URL, json={**KID, "name": n})).status_code == 201
    listed = (await client.get(URL)).json()
    assert [m["name"] for m in listed[1:]] == names


async def test_create_rejects_self(client, consented):
    r = await client.post(URL, json={**KID, "relation": "self"})
    assert r.status_code == 422
    assert _err(r)["code"] == "validation_error"
    assert _err(r)["details"]["fields"] == ["body.relation"]


async def test_create_requires_birth_year(client, consented):
    r = await client.post(URL, json={"name": "Riya", "relation": "child"})
    assert r.status_code == 422 and "body.birth_year" in _err(r)["details"]["fields"]


@pytest.mark.parametrize("delta", [1, 2])
async def test_birth_year_cannot_be_in_the_future(client, consented, delta):
    r = await client.post(URL, json={**KID, "birth_year": today_ist().year + delta})
    assert r.status_code == 422 and "body.birth_year" in _err(r)["details"]["fields"]


async def test_birth_year_bounds(client, consented):
    assert (await client.post(URL, json={**KID, "birth_year": 1899})).status_code == 422
    assert (await client.post(URL, json={**KID, "birth_year": 1900})).status_code == 201
    this_year = today_ist().year
    assert (await client.post(URL, json={**KID, "birth_year": this_year})).status_code == 201


async def test_name_is_stripped_and_bounded(client, consented):
    r = await client.post(URL, json={**KID, "name": "  Ravi  "})
    assert r.status_code == 201 and r.json()["name"] == "Ravi"
    assert (await client.post(URL, json={**KID, "name": "   "})).status_code == 422
    assert (await client.post(URL, json={**KID, "name": "x" * 41})).status_code == 422
    assert (await client.post(URL, json={**KID, "name": "x" * 40})).status_code == 201


async def test_height_weight_bounds(client, consented):
    assert (await client.post(URL, json={**KID, "height_cm": 29})).status_code == 422
    assert (await client.post(URL, json={**KID, "height_cm": 251})).status_code == 422
    assert (await client.post(URL, json={**KID, "weight_kg": 1.9})).status_code == 422
    assert (await client.post(URL, json={**KID, "weight_kg": 301})).status_code == 422
    r = await client.post(URL, json={**KID, "height_cm": 120.5, "weight_kg": 22})
    assert r.status_code == 201
    assert r.json()["height_cm"] == 120.5 and r.json()["weight_kg"] == 22


async def test_unknown_condition_and_goal_rejected(client, consented):
    assert (await client.post(URL, json={**KID, "conditions": ["cancer"]})).status_code == 422
    assert (await client.post(URL, json={**KID, "goal": "bulk"})).status_code == 422


async def test_member_limit(client, consented, count_members):
    for i in range(9):  # the primary plus 9 = 10
        r = await client.post(URL, json={**KID, "name": f"M{i}"})
        assert r.status_code == 201, r.json()
    r = await client.post(URL, json={**KID, "name": "Eleventh"})
    assert r.status_code == 422 and _err(r)["code"] == "member_limit"
    assert _err(r)["message_key"] == "error.member_limit"
    assert await count_members(ACC_A) == 10


# --- consent gate -----------------------------------------------------------------------------


async def test_conditions_require_consent(client, login, db_session, count_members):
    login(ACC_B)
    r = await client.post(URL, json={**KID, "relation": "parent", "conditions": ["diabetes"]})
    assert r.status_code == 403
    assert _err(r)["code"] == "consent_required"
    assert _err(r)["message_key"] == "error.consent_required"
    assert await list_members(db_session, ACC_B) == []
    assert await count_members(ACC_B) == 0  # not even the primary was written


@pytest.mark.parametrize(
    "field",
    [
        {"allergens": ["peanut"]},
        {"allergens": ["kiwi"]},
        {"conditions": ["pcos"]},
        {"goal": "weight_loss"},
        {"height_cm": 120},
        {"weight_kg": 25},
    ],
)
async def test_each_health_field_requires_consent(client, login, count_members, field):
    login(ACC_B)
    r = await client.post(URL, json={**KID, **field})
    assert r.status_code == 403 and _err(r)["code"] == "consent_required"
    assert await count_members(ACC_B) == 0


async def test_non_health_fields_need_no_consent(client, login):
    login(ACC_B)
    body = {
        **KID,
        "sex": "female",
        "diet": "jain",
        "custom_alerts": ["palm_oil"],
        "allergens": [],
        "conditions": [],
        "goal": None,
        "height_cm": None,
        "weight_kg": None,
    }
    r = await client.post(URL, json=body)
    assert r.status_code == 201
    assert r.json()["diet"] == "jain" and r.json()["custom_alerts"] == ["palm_oil"]


async def test_health_data_consent_alone_is_enough(client, login, grant):
    await grant(ACC_B, ["health_data"])
    login(ACC_B)
    r = await client.post(URL, json={**KID, "allergens": ["peanut"], "conditions": ["diabetes"]})
    assert r.status_code == 201
    assert r.json()["allergens"] == ["peanut"] and r.json()["conditions"] == ["diabetes"]


async def test_ai_processing_does_not_unlock_health_fields(client, login, grant, count_members):
    await grant(ACC_B, ["terms", "ai_processing"])
    login(ACC_B)
    r = await client.post(URL, json={**KID, "allergens": ["peanut"]})
    assert r.status_code == 403 and _err(r)["code"] == "consent_required"
    assert await count_members(ACC_B) == 0


async def test_old_version_consent_does_not_count(client, login, grant):
    await grant(ACC_B, ["health_data"], version="2020-01-01")
    login(ACC_B)
    r = await client.post(URL, json={**KID, "allergens": ["peanut"]})
    assert r.status_code == 403


async def test_withdrawn_consent_blocks_new_health_data_but_keeps_stored(
    client, consented, db_session
):
    created = (await client.post(URL, json={**KID, "allergens": ["milk"]})).json()
    r = await client.post(
        "/v1/consents", json={"purpose": "health_data", "version": "2026-11-01", "granted": False}
    )
    assert r.status_code == 200
    r = await client.patch(f"{URL}/{created['id']}", json={"allergens": ["milk", "egg"]})
    assert r.status_code == 403
    listed = {m["id"]: m for m in (await client.get(URL)).json()}
    assert listed[created["id"]]["allergens"] == ["milk"]  # withdrawal deletes nothing (M3)


async def test_patch_name_only_without_consent(client, login, add_member, db_session):
    member = await add_member(ACC_B, allergens=["peanut"], conditions=["diabetes"])
    login(ACC_B)
    r = await client.patch(f"{URL}/{member.id}", json={"name": "Papa"})
    assert r.status_code == 200
    assert r.json()["name"] == "Papa"
    assert r.json()["allergens"] == ["peanut"] and r.json()["conditions"] == ["diabetes"]


async def test_patch_adding_allergen_without_consent_changes_nothing(
    client, login, add_member, db_session
):
    member = await add_member(ACC_B, allergens=[], conditions=[])
    login(ACC_B)
    r = await client.patch(f"{URL}/{member.id}", json={"name": "Changed", "allergens": ["peanut"]})
    assert r.status_code == 403 and _err(r)["code"] == "consent_required"
    row = await _row(db_session, member.id)
    assert row.name == "Ravi" and row.allergens == []


async def test_patch_clearing_health_fields_needs_no_consent(client, login, add_member):
    member = await add_member(ACC_B, conditions=["diabetes"], goal="weight_loss", height_cm=170)
    login(ACC_B)
    r = await client.patch(
        f"{URL}/{member.id}", json={"conditions": [], "goal": None, "height_cm": None}
    )
    assert r.status_code == 200
    assert r.json()["conditions"] == [] and r.json()["goal"] is None
    assert r.json()["height_cm"] is None


# --- allergens and custom alerts ---------------------------------------------------------------


async def test_free_text_allergens_round_trip(client, consented, db_session):
    allergens = ["kiwi", "मूंगफली", "  Peanut ", " Kiwi Fruit "]
    r = await client.post(URL, json={**KID, "allergens": allergens})
    assert r.status_code == 201
    expected = ["kiwi", "मूंगफली", "peanut", "Kiwi Fruit"]
    assert r.json()["allergens"] == expected
    listed = {m["id"]: m for m in (await client.get(URL)).json()}
    assert listed[r.json()["id"]]["allergens"] == expected
    assert (await _row(db_session, r.json()["id"])).allergens == expected


async def test_allergens_deduplicated_keeping_order(client, consented):
    r = await client.post(URL, json={**KID, "allergens": ["kiwi", "KIWI", "milk", "Milk", "kiwi"]})
    assert r.status_code == 201 and r.json()["allergens"] == ["kiwi", "milk"]


@pytest.mark.parametrize(
    "allergens",
    [["x"], ["  "], ["y" * 41], [f"food{i}" for i in range(21)]],
)
async def test_invalid_allergens_422(client, consented, allergens):
    r = await client.post(URL, json={**KID, "allergens": allergens})
    assert r.status_code == 422 and _err(r)["code"] == "validation_error"


async def test_twenty_allergens_accepted(client, consented):
    allergens = [f"food{i}" for i in range(20)]
    r = await client.post(URL, json={**KID, "allergens": allergens})
    assert r.status_code == 201 and r.json()["allergens"] == allergens


async def test_allergens_nfc_normalised_before_dedupe(client, consented):
    """Composed and decomposed forms of the same text are one allergen (Ruling P8.3)."""
    composed, decomposed = "caf\u00e9", "cafe\u0301"
    nukta_pre = "\u095b\u093e\u092b\u093c\u0930\u093e\u0928"  # precomposed ज़ (U+095B)
    nukta_dec = "\u091c\u093c\u093e\u092b\u093c\u0930\u093e\u0928"
    r = await client.post(
        URL, json={**KID, "allergens": [composed, decomposed, nukta_pre, nukta_dec]}
    )
    assert r.status_code == 201
    stored = r.json()["allergens"]
    assert len(stored) == 2
    assert all(unicodedata.is_normalized("NFC", a) for a in stored)
    assert stored[0] == unicodedata.normalize("NFC", composed)


async def test_invalid_custom_alert_422(client, consented):
    r = await client.post(URL, json={**KID, "custom_alerts": ["glitter"]})
    assert r.status_code == 422 and _err(r)["code"] == "validation_error"


async def test_custom_alerts_saved_and_deduplicated(client, consented):
    r = await client.post(URL, json={**KID, "custom_alerts": ["maida", "palm_oil", "maida"]})
    assert r.status_code == 201 and r.json()["custom_alerts"] == ["maida", "palm_oil"]


# --- get, patch, delete ------------------------------------------------------------------------


async def test_get_and_patch(client, consented):
    created = (await client.post(URL, json=KID)).json()
    got = await client.get(f"{URL}/{created['id']}")
    assert got.status_code == 200 and got.json() == created
    r = await client.patch(
        f"{URL}/{created['id']}",
        json={"allergens": ["sesame"], "conditions": ["hypertension"], "goal": "healthy_eating"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["allergens"] == ["sesame"] and body["conditions"] == ["hypertension"]
    assert body["name"] == "Riya" and body["birth_year"] == 2018  # untouched fields kept


async def test_patch_null_leaves_required_fields_unchanged(client, consented):
    """The generated Dart client sends unset fields as null: that must not clear or fail."""
    created = await client.post(URL, json={**KID, "allergens": ["milk"], "goal": "weight_gain"})
    created = created.json()
    nulls = {f: None for f in ("birth_year", "relation", "diet", "allergens", "conditions")}
    r = await client.patch(
        f"{URL}/{created['id']}", json={**nulls, "custom_alerts": None, "name": "Riya K"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Riya K" and body["birth_year"] == 2018
    assert body["relation"] == "child" and body["allergens"] == ["milk"]
    assert body["goal"] == "weight_gain"  # not sent, so kept


async def test_patch_null_clears_optional_fields(client, consented):
    created = (await client.post(URL, json={**KID, "sex": "female", "height_cm": 120})).json()
    r = await client.patch(f"{URL}/{created['id']}", json={"sex": None, "height_cm": None})
    assert r.status_code == 200
    assert r.json()["sex"] is None and r.json()["height_cm"] is None


async def test_patch_resending_stored_health_fields_needs_no_consent(client, login, add_member):
    """A client that sends the whole form can still rename after consent is withdrawn."""
    member = await add_member(
        ACC_B, allergens=["peanut", "kiwi"], conditions=["diabetes"], height_cm=170.0, goal=None
    )
    login(ACC_B)
    body = {
        "name": "Papa",
        "allergens": ["peanut", "kiwi"],
        "conditions": ["diabetes"],
        "height_cm": 170,
        "weight_kg": None,
        "goal": None,
    }
    r = await client.patch(f"{URL}/{member.id}", json=body)
    assert r.status_code == 200 and r.json()["name"] == "Papa"


async def test_patch_removing_stored_allergens_needs_no_consent(
    client, login, add_member, db_session
):
    """A strict subset of the stored list writes no new health data (Ruling P8.1)."""
    member = await add_member(ACC_B, allergens=["peanut", "kiwi"], conditions=["diabetes", "pcos"])
    login(ACC_B)
    r = await client.patch(
        f"{URL}/{member.id}", json={"allergens": ["peanut"], "conditions": ["pcos"]}
    )
    assert r.status_code == 200
    row = await _row(db_session, member.id)
    assert row.allergens == ["peanut"] and row.conditions == ["pcos"]


async def test_patch_replacing_stored_allergens_without_consent_is_403(
    client, login, add_member, db_session
):
    member = await add_member(ACC_B, allergens=["peanut", "kiwi"])
    login(ACC_B)
    r = await client.patch(f"{URL}/{member.id}", json={"allergens": ["peanut", "sesame"]})
    assert r.status_code == 403 and _err(r)["code"] == "consent_required"
    assert (await _row(db_session, member.id)).allergens == ["peanut", "kiwi"]


async def test_patch_removal_plus_addition_of_conditions_is_403(client, login, add_member):
    member = await add_member(ACC_B, conditions=["diabetes", "pcos"])
    login(ACC_B)
    r = await client.patch(f"{URL}/{member.id}", json={"conditions": ["hypertension"]})
    assert r.status_code == 403


async def test_patch_cannot_make_a_member_self(client, consented):
    created = (await client.post(URL, json=KID)).json()
    r = await client.patch(f"{URL}/{created['id']}", json={"relation": "self"})
    assert r.status_code == 422 and _err(r)["details"]["fields"] == ["body.relation"]


async def test_primary_relation_is_fixed(client, consented):
    primary = (await client.get(URL)).json()[0]
    r = await client.patch(f"{URL}/{primary['id']}", json={"relation": "parent"})
    assert r.status_code == 422 and _err(r)["details"]["fields"] == ["body.relation"]
    r = await client.patch(
        f"{URL}/{primary['id']}", json={"relation": "self", "birth_year": 1990, "name": "Asha"}
    )
    assert r.status_code == 200
    assert r.json()["birth_year"] == 1990 and r.json()["is_primary"] is True


async def test_delete_member(client, consented, count_members):
    created = (await client.post(URL, json=KID)).json()
    r = await client.delete(f"{URL}/{created['id']}")
    assert r.status_code == 204 and r.content == b""
    assert (await client.get(f"{URL}/{created['id']}")).status_code == 404
    assert await count_members(ACC_A) == 1


async def test_delete_primary_rejected(client, consented, count_members):
    primary = (await client.get(URL)).json()[0]
    r = await client.delete(f"{URL}/{primary['id']}")
    assert r.status_code == 422 and _err(r)["code"] == "primary_member"
    assert _err(r)["message_key"] == "error.primary_member"
    assert await count_members(ACC_A) == 1


async def test_other_account_member_is_404(client, consented, other_account_member_id, db_session):
    before = await _row(db_session, other_account_member_id)
    snapshot = (before.name, list(before.allergens), list(before.conditions))
    mid = other_account_member_id
    calls = [
        client.get(f"{URL}/{mid}"),
        client.patch(f"{URL}/{mid}", json={"name": "x"}),
        client.patch(f"{URL}/{mid}", json={"allergens": ["egg"], "conditions": []}),
        client.delete(f"{URL}/{mid}"),
    ]
    for call in calls:
        r = await call
        assert r.status_code == 404 and _err(r)["code"] == "member_not_found"
    after = await _row(db_session, mid)
    assert after is not None
    assert (after.name, list(after.allergens), list(after.conditions)) == snapshot
    # And ACC_A's list never shows it.
    assert mid not in {m["id"] for m in (await client.get(URL)).json()}


async def test_foreign_404_matches_unknown_404(client, consented, other_account_member_id):
    foreign = await client.patch(f"{URL}/{other_account_member_id}", json={"name": "x"})
    unknown = await client.patch(f"{URL}/{uuid4()}", json={"name": "x"})
    assert foreign.status_code == unknown.status_code == 404
    assert foreign.json() == unknown.json()


async def test_foreign_404_without_consent_too(client, login, other_account_member_id):
    """Ownership is checked before the consent gate, so 403 never confirms a foreign id."""
    login(ACC_B)
    r = await client.patch(f"{URL}/{other_account_member_id}", json={"allergens": ["egg"]})
    assert r.status_code == 404 and _err(r)["code"] == "member_not_found"


async def test_requires_auth(client):
    mid = uuid4()
    for r in (
        await client.get(URL),
        await client.post(URL, json=KID),
        await client.get(f"{URL}/{mid}"),
        await client.patch(f"{URL}/{mid}", json={"name": "x"}),
        await client.delete(f"{URL}/{mid}"),
    ):
        assert r.status_code == 401


async def test_created_member_is_never_primary(client, consented, db_session):
    await client.post(URL, json=KID)
    primaries = await db_session.scalar(
        text("select count(*) from members where account_id = :a and is_primary"), {"a": ACC_A}
    )
    assert primaries == 1


def test_openapi_documents_routes_and_403(app):
    spec = app.openapi()
    ops = {
        (path, method): op["operationId"]
        for path, item in spec["paths"].items()
        if path.startswith("/v1/members")
        for method, op in item.items()
    }
    assert ops == {
        ("/v1/members", "get"): "members_list",
        ("/v1/members", "post"): "members_create",
        ("/v1/members/{member_id}", "get"): "members_get",
        ("/v1/members/{member_id}", "patch"): "members_update",
        ("/v1/members/{member_id}", "delete"): "members_delete",
    }
    for method in ("post", "patch"):
        path = "/v1/members" if method == "post" else "/v1/members/{member_id}"
        content = spec["paths"][path][method]["responses"]["403"]["content"]
        assert content["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }

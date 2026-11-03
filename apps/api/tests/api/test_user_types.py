"""Plan 9 Tasks 1 and 2: account user types (P9-R1..R4, R8, R9).

A user type is presentation only. It never changes a verdict, never reaches analytics, and
never writes member data: pre-fill only *suggests* changes, which the client applies through
`PATCH /v1/members/{id}` after the user confirms.
"""

import re
from collections.abc import Iterable
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from sqlalchemy import func, select, text

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.consents.models import Consent
from app.features.consents.policy import CURRENT_VERSIONS
from app.features.me.service import ensure_account
from app.features.members.models import Member
from app.features.members.service import get_or_create_primary
from app.integrations import posthog
from app.integrations.callmissed import get_llm_provider
from app.integrations.openfoodfacts import get_off_client
from scripts.export_fixture_responses import fixture_product_record

A = UUID("11111111-1111-1111-1111-111111111111")
B = UUID("22222222-2222-2222-2222-222222222222")
URL = "/v1/me/user-types"
ACTIVE = "/v1/me/user-types/active"
ALL_PURPOSES = ("terms", "health_data", "ai_processing")


class _NoOff:
    async def get_product(self, barcode):  # pragma: no cover - never called with product_id
        raise AssertionError("no OFF call expected")


class _NoCallLLM:
    async def chat_json(self, **kwargs):  # pragma: no cover
        raise AssertionError("no LLM call without ai_processing consent")

    async def extract_label(self, **kwargs):  # pragma: no cover
        raise AssertionError("not used")


@pytest.fixture
def login(app, db_session):
    def _login(account_id: UUID = A) -> None:
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[current_account] = lambda: AccountContext(
            account_id, "asha@example.com"
        )
        app.dependency_overrides[get_off_client] = lambda: _NoOff()
        app.dependency_overrides[get_llm_provider] = lambda: _NoCallLLM()

    return _login


@pytest.fixture
def grant(db_session):
    async def _grant(account_id: UUID = A, purposes: Iterable[str] = ALL_PURPOSES) -> None:
        await ensure_account(db_session, AccountContext(account_id, None))
        for purpose in purposes:
            db_session.add(
                Consent(account_id=account_id, purpose=purpose, version=CURRENT_VERSIONS[purpose])
            )
        await db_session.flush()

    return _grant


def _err(r) -> dict:
    return r.json()["error"]


async def _row_count(db_session, account_id: UUID) -> int:
    return (
        await db_session.execute(
            text("select count(*) from account_user_types where account_id = :a"),
            {"a": account_id},
        )
    ).scalar_one()


async def _primary(db_session, account_id: UUID) -> Member:
    await ensure_account(db_session, AccountContext(account_id, None))
    member = await get_or_create_primary(db_session, account_id)
    await db_session.flush()
    return member


async def _fresh(db_session, member_id: UUID) -> Member:
    return await db_session.scalar(
        select(Member).where(Member.id == member_id).execution_options(populate_existing=True)
    )


# --- Task 1: GET / PUT / PATCH active ---------------------------------------------------------


async def test_get_without_row_is_unanswered_eat_better(client, login, db_session):
    login(A)
    r = await client.get(URL)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["types"] == [] and body["answered"] is False and body["answered_at"] is None
    assert body["active_type"] == "eat_better"
    assert body["prefill"] is None
    assert await _row_count(db_session, A) == 0  # a GET never writes the row


async def test_put_roundtrip_and_resolved_active_type(client, login, grant):
    await grant(A)
    login(A)
    body = {
        "types": ["gym", "allergy_diet"],
        "follow_ups": {"gym_goal": "stay_fit", "allergens": ["peanut"], "diet": "veg"},
    }
    r = await client.put(URL, json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["types"] == ["gym", "allergy_diet"]  # the user's tap order
    assert out["active_type"] == "allergy_diet"  # safety-first priority (P9-R4)
    assert out["answered"] is True and out["answered_at"] is not None
    assert out["follow_ups"]["gym_goal"] == "stay_fit"
    assert out["follow_ups"]["allergens"] == ["peanut"]
    assert out["follow_ups"]["diet"] == "veg"
    got = (await client.get(URL)).json()
    assert got["types"] == out["types"] and got["follow_ups"] == out["follow_ups"]
    assert got["active_type"] == "allergy_diet"


async def test_skip_stores_empty_and_answered(client, login, db_session):
    login(A)
    r = await client.put(URL, json={"types": []})
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["types"] == [] and out["answered"] is True
    assert out["active_type"] == "eat_better"
    assert await _row_count(db_session, A) == 1
    assert (await client.get(URL)).json()["answered"] is True


@pytest.mark.parametrize(
    "body",
    [
        {"types": ["gym", "family", "weight_loss", "eat_better"]},
        {"types": ["gym", "gym"]},
        {"types": ["family"], "follow_ups": {"family_with": ["children", "children"]}},
        {"types": ["eat_better"], "follow_ups": {"alerts": ["palm_oil", "palm_oil"]}},
        {"types": ["not_a_type"]},
        {"types": ["gym"], "follow_ups": {"gym_goal": "bulk"}},
        {"types": ["gym"], "follow_ups": {"unknown_key": 1}},
    ],
)
async def test_more_than_three_or_duplicates_422(client, login, grant, db_session, body):
    await grant(A)
    login(A)
    r = await client.put(URL, json=body)
    assert r.status_code == 422, r.text
    assert _err(r)["code"] == "validation_error"
    assert await _row_count(db_session, A) == 0


@pytest.mark.parametrize(
    "body",
    [
        {"types": ["family"], "follow_ups": {"gym_goal": "build_muscle"}},
        {"types": ["gym"], "follow_ups": {"family_with": ["children"]}},
        {"types": ["gym"], "follow_ups": {"alerts": ["palm_oil"]}},
        {"types": ["weight_loss"], "follow_ups": {"allergens": ["milk"]}},
        {"types": ["weight_loss"], "follow_ups": {"diet": "veg"}},
        {"types": ["allergy_diet"], "follow_ups": {"conditions": ["diabetes"]}},
        {"types": [], "follow_ups": {"gym_goal": "stay_fit"}},
    ],
)
async def test_follow_up_without_type_422(client, login, grant, db_session, body):
    await grant(A)
    login(A)
    r = await client.put(URL, json=body)
    assert r.status_code == 422, r.text
    assert _err(r) == {
        "code": "follow_up_without_type",
        "message_key": "error.follow_up_without_type",
        "details": {},
    }
    assert await _row_count(db_session, A) == 0


@pytest.mark.parametrize(
    "body",
    [
        {"types": ["health_condition"], "follow_ups": {"conditions": ["diabetes"]}},
        {"types": ["health_condition"]},
        {"types": ["weight_loss"]},
        {"types": ["allergy_diet"]},
        {"types": ["allergy_diet"], "follow_ups": {"allergens": ["milk"]}},
        {"types": ["family"], "follow_ups": {"conditions": ["diabetes"]}},
        {"types": ["gym", "weight_loss"], "follow_ups": {"gym_goal": "lose_fat"}},
    ],
)
async def test_health_type_without_consent_403_writes_nothing(
    client, login, grant, db_session, body
):
    await grant(A, ["terms", "ai_processing"])  # everything except health_data
    login(A)
    r = await client.put(URL, json=body)
    assert r.status_code == 403, r.text
    assert _err(r) == {
        "code": "consent_required",
        "message_key": "error.consent_required",
        "details": {"purposes": ["health_data"]},
    }
    assert await _row_count(db_session, A) == 0


async def test_health_type_with_withdrawn_consent_403(client, login, grant, db_session):
    await grant(A)
    await db_session.execute(
        text("update consents set withdrawn_at = now() where account_id = :a"), {"a": A}
    )
    login(A)
    r = await client.put(URL, json={"types": ["weight_loss"]})
    assert r.status_code == 403 and _err(r)["details"] == {"purposes": ["health_data"]}


async def test_gym_and_family_need_no_health_consent(client, login, db_session):
    login(A)  # no consent at all
    body = {
        "types": ["gym", "family", "eat_better"],
        "follow_ups": {
            "gym_goal": "build_muscle",
            "family_with": ["children", "parents"],
            "alerts": ["palm_oil"],
        },
    }
    r = await client.put(URL, json=body)
    assert r.status_code == 200, r.text
    assert r.json()["types"] == ["gym", "family", "eat_better"]
    assert r.json()["active_type"] == "family"


async def test_put_keeps_active_type_only_while_selected(client, login, grant):
    await grant(A)
    login(A)
    await client.put(URL, json={"types": ["gym", "family"]})
    r = await client.patch(ACTIVE, json={"active_type": "gym"})
    assert r.status_code == 200 and r.json()["active_type"] == "gym"
    # Still selected: kept.
    r = await client.put(URL, json={"types": ["weight_loss", "gym"]})
    assert r.json()["active_type"] == "gym"
    # No longer selected: back to the resolved default.
    r = await client.put(URL, json={"types": ["weight_loss", "family"]})
    assert r.json()["active_type"] == "family"


async def test_set_active_must_be_selected_422(client, login):
    login(A)
    r = await client.patch(ACTIVE, json={"active_type": "gym"})
    assert r.status_code == 404 and _err(r)["code"] == "user_types_not_found"

    await client.put(URL, json={"types": ["gym", "family"]})
    r = await client.patch(ACTIVE, json={"active_type": "weight_loss"})
    assert r.status_code == 422 and _err(r)["code"] == "user_type_not_selected"
    r = await client.patch(ACTIVE, json={"active_type": "eat_better"})
    assert r.status_code == 422 and _err(r)["code"] == "user_type_not_selected"
    r = await client.patch(ACTIVE, json={"active_type": "family"})
    assert r.status_code == 200 and r.json()["active_type"] == "family"
    assert (await client.get(URL)).json()["active_type"] == "family"

    await client.put(URL, json={"types": []})
    r = await client.patch(ACTIVE, json={"active_type": "eat_better"})
    assert r.status_code == 200 and r.json()["active_type"] == "eat_better"
    r = await client.patch(ACTIVE, json={"active_type": "gym"})
    assert r.status_code == 422 and _err(r)["code"] == "user_type_not_selected"
    r = await client.patch(ACTIVE, json={"active_type": "no_such"})
    assert r.status_code == 422 and _err(r)["code"] == "validation_error"


async def test_set_active_after_withdrawal_ok(client, login, grant, db_session):
    await grant(A)
    login(A)
    r = await client.put(
        URL,
        json={"types": ["health_condition", "gym"], "follow_ups": {"conditions": ["diabetes"]}},
    )
    assert r.status_code == 200, r.text
    await db_session.execute(
        text(
            "update consents set withdrawn_at = now() "
            "where account_id = :a and purpose = 'health_data'"
        ),
        {"a": A},
    )
    r = await client.patch(ACTIVE, json={"active_type": "gym"})
    assert r.status_code == 200, r.text
    body = (await client.get(URL)).json()
    # Withdrawal stops processing, it doesn't erase (ADR 0018); the stored types still drive
    # the layout.
    assert body["types"] == ["health_condition", "gym"] and body["active_type"] == "gym"
    assert body["follow_ups"]["conditions"] == ["diabetes"]


async def test_removing_types_keeps_member_fields(client, login, grant, db_session):
    await grant(A)
    me = await _primary(db_session, A)
    me.allergens, me.conditions, me.diet = ["peanut"], ["diabetes"], "veg"
    me.goal, me.custom_alerts = "weight_loss", ["palm_oil"]
    await db_session.flush()
    login(A)
    r = await client.put(
        URL,
        json={"types": ["health_condition"], "follow_ups": {"conditions": ["diabetes"]}},
    )
    assert r.status_code == 200
    r = await client.put(URL, json={"types": []})
    assert r.status_code == 200
    after = await _fresh(db_session, me.id)
    assert after.allergens == ["peanut"] and after.conditions == ["diabetes"]
    assert after.diet == "veg" and after.goal == "weight_loss"
    assert after.custom_alerts == ["palm_oil"]


async def test_other_accounts_row_is_invisible(client, login):
    login(A)
    assert (await client.put(URL, json={"types": ["gym"]})).status_code == 200
    login(B)
    body = (await client.get(URL)).json()
    assert body["answered"] is False and body["types"] == []
    r = await client.patch(ACTIVE, json={"active_type": "gym"})
    assert r.status_code == 404 and _err(r)["code"] == "user_types_not_found"
    login(A)
    assert (await client.get(URL)).json()["types"] == ["gym"]


async def test_user_types_require_auth(client):
    assert (await client.get(URL)).status_code == 401
    assert (await client.put(URL, json={"types": []})).status_code == 401
    assert (await client.patch(ACTIVE, json={"active_type": "gym"})).status_code == 401


def test_openapi_operation_ids(app):
    paths = app.openapi()["paths"]
    assert paths[URL]["get"]["operationId"] == "me_user_types_get"
    assert paths[URL]["put"]["operationId"] == "me_user_types_put"
    assert paths[ACTIVE]["patch"]["operationId"] == "me_user_types_set_active"
    assert "403" in paths[URL]["put"]["responses"]


async def _seed_family(db_session, account_id: UUID) -> dict[str, UUID]:
    """Me (primary, 1991), Dad (1954, veg, diabetes), Riya (2018, veg, milk allergy)."""
    me = await _primary(db_session, account_id)
    me.name, me.birth_year = "Me", 1991
    dad = Member(
        account_id=account_id,
        name="Dad",
        relation="parent",
        birth_year=1954,
        diet="veg",
        conditions=["diabetes"],
        weight_kg=70,
        created_at=func.clock_timestamp(),
    )
    db_session.add(dad)
    await db_session.flush()
    riya = Member(
        account_id=account_id,
        name="Riya",
        relation="child",
        birth_year=2018,
        diet="veg",
        allergens=["milk"],
        created_at=func.clock_timestamp(),
    )
    db_session.add(riya)
    await db_session.flush()
    return {"me": me.id, "dad": dad.id, "riya": riya.id}


async def test_user_types_never_change_verdicts(client, login, grant, db_session):
    product = fixture_product_record("sf_biscuit")
    db_session.add(product)
    await db_session.flush()
    families = {}
    for account_id, body in (
        (A, {"types": ["gym"], "follow_ups": {"gym_goal": "build_muscle"}}),
        (
            B,
            {
                "types": ["health_condition", "allergy_diet", "family"],
                "follow_ups": {
                    "conditions": ["diabetes", "pcos"],
                    "allergens": ["peanut"],
                    "diet": "jain",
                    "family_with": ["children"],
                },
            },
        ),
    ):
        await grant(account_id, ["terms", "health_data"])  # no ai_processing: no LLM call
        families[account_id] = await _seed_family(db_session, account_id)
        login(account_id)
        assert (await client.put(URL, json=body)).status_code == 200

    def responses_for(account_id: UUID):
        async def _get() -> tuple[str, str, str]:
            login(account_id)
            fam = families[account_id]
            meal = await client.post(
                "/v1/meals",
                json={"member_id": str(fam["dad"]), "product_id": str(product.id), "servings": 1},
            )
            assert meal.status_code == 201, meal.text
            r = await client.post("/v1/analyze", json={"product_id": str(product.id)})
            assert r.status_code == 200, r.text
            s = await client.get(f"/v1/meals/summary?member_id={fam['dad']}&period=day")
            assert s.status_code == 200, s.text
            return r.text, s.text, r.json()["scan_id"]

        return _get

    analyze_a, summary_a, scan_a = await responses_for(A)()
    analyze_b, summary_b, scan_b = await responses_for(B)()

    def normalise(body: str, account_id: UUID, scan_id: str) -> str:
        body = body.replace(scan_id, "SCAN")
        for key, member_id in families[account_id].items():
            body = body.replace(str(member_id), key.upper())
        return body

    assert normalise(analyze_a, A, scan_a) == normalise(analyze_b, B, scan_b)
    assert normalise(summary_a, A, scan_a) == normalise(summary_b, B, scan_b)
    assert '"verdicts"' in analyze_a and "RIYA" in normalise(analyze_a, A, scan_a)


async def test_no_analytics_for_user_types(client, login, grant, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr(posthog, "_client", sent)
    tracked = MagicMock()
    monkeypatch.setattr(posthog, "track", tracked)
    import app.features.me.router as me_router

    if hasattr(me_router, "track"):
        monkeypatch.setattr(me_router, "track", tracked)
    await grant(A)
    login(A)
    await client.get(URL)
    await client.put(URL, json={"types": ["weight_loss", "gym"]})
    await client.patch(ACTIVE, json={"active_type": "gym"})
    await client.put(URL, json={"types": []})
    tracked.assert_not_called()
    sent.capture.assert_not_called()
    banned = re.compile(r"type|goal|focus")
    for event, props in posthog.ALLOWED_EVENTS.items():
        assert not banned.search(event), event
        assert not any(banned.search(p) for p in props), (event, props)


async def test_user_types_logs_no_types(client, login, grant, caplog):
    await grant(A)
    login(A)
    with caplog.at_level("DEBUG"):
        r = await client.put(
            URL,
            json={"types": ["health_condition"], "follow_ups": {"conditions": ["diabetes"]}},
        )
    assert r.status_code == 200
    text_ = caplog.text
    assert "user_types status=saved count=1" in text_
    assert "health_condition" not in text_ and "diabetes" not in text_


# --- Task 2: pre-fill suggestions (P9-R9) ----------------------------------------------------

FULL = {
    "types": ["health_condition", "allergy_diet", "eat_better"],
    "follow_ups": {
        "conditions": ["diabetes"],
        "allergens": ["milk"],
        "diet": "veg",
        "alerts": ["palm_oil"],
    },
}


async def test_put_returns_prefill_for_primary_only(client, login, grant, db_session):
    await grant(A)
    me = await _primary(db_session, A)
    me.allergens = ["peanut"]
    other = Member(account_id=A, name="Dad", relation="parent", birth_year=1950, diet="non_veg")
    db_session.add(other)
    await db_session.flush()
    login(A)
    r = await client.put(URL, json=FULL)
    assert r.status_code == 200, r.text
    prefill = r.json()["prefill"]
    assert prefill["member_id"] == str(me.id) and prefill["member_id"] != str(other.id)
    changes = {c["field"]: c for c in prefill["changes"]}
    assert set(changes) == {"conditions", "allergens", "diet", "goal", "custom_alerts"}
    assert changes["allergens"] == {
        "field": "allergens",
        "current": ["peanut"],
        "value": ["peanut", "milk"],
        "added": ["milk"],
        "reason": "allergy_diet",
    }
    assert changes["diet"]["value"] == "veg" and changes["diet"]["current"] == "non_veg"
    assert changes["goal"]["value"] == "healthy_eating"
    assert prefill["goal_choice"] is None
    assert prefill["needs_health_consent"] is False
    # GET recomputes the same suggestions.
    assert (await client.get(URL)).json()["prefill"] == prefill


async def test_prefill_is_not_applied(client, login, grant, db_session):
    await grant(A)
    me = await _primary(db_session, A)
    login(A)
    assert (await client.put(URL, json=FULL)).status_code == 200
    await client.get(URL)
    after = await _fresh(db_session, me.id)
    assert after.allergens == [] and after.conditions == [] and after.custom_alerts == []
    assert after.diet == "non_veg" and after.goal is None


async def test_prefill_empty_after_confirm(client, login, grant, db_session):
    await grant(A)
    login(A)
    prefill = (await client.put(URL, json=FULL)).json()["prefill"]
    patch = {c["field"]: c["value"] for c in prefill["changes"]}
    r = await client.patch(f"/v1/members/{prefill['member_id']}", json=patch)
    assert r.status_code == 200, r.text
    again = (await client.get(URL)).json()["prefill"]
    assert again["changes"] == [] and again["goal_choice"] is None
    assert again["member_id"] == prefill["member_id"]


async def test_prefill_for_skip_and_family_is_empty(client, login):
    login(A)
    for body in ({"types": []}, {"types": ["family"], "follow_ups": {"family_with": ["parents"]}}):
        prefill = (await client.put(URL, json=body)).json()["prefill"]
        assert prefill["changes"] == [] and prefill["goal_choice"] is None
        assert prefill["needs_health_consent"] is False


async def test_needs_health_consent_flag(client, login, grant, db_session):
    await grant(A)
    login(A)
    r = await client.put(URL, json={"types": ["weight_loss"]})
    assert r.json()["prefill"]["needs_health_consent"] is False
    await db_session.execute(
        text(
            "update consents set withdrawn_at = now() "
            "where account_id = :a and purpose = 'health_data'"
        ),
        {"a": A},
    )
    prefill = (await client.get(URL)).json()["prefill"]
    assert [c["field"] for c in prefill["changes"]] == ["goal"]
    assert prefill["needs_health_consent"] is True
    # The members route keeps its own gate: confirming the goal without consent is refused.
    r = await client.patch(f"/v1/members/{prefill['member_id']}", json={"goal": "weight_loss"})
    assert r.status_code == 403


async def test_needs_health_consent_false_for_non_health_fields(client, login, db_session):
    login(A)  # no consent at all; diet and custom alerts are not health fields
    prefill = (
        await client.put(URL, json={"types": ["eat_better"], "follow_ups": {"alerts": ["msg"]}})
    ).json()["prefill"]
    fields = [c["field"] for c in prefill["changes"]]
    assert fields == ["goal", "custom_alerts"] or fields == ["custom_alerts", "goal"]
    # `goal` is a health field (HEALTH_FIELDS), so the flag is set.
    assert prefill["needs_health_consent"] is True
    me = await _primary(db_session, A)
    me.goal = "weight_gain"
    await db_session.flush()
    prefill = (await client.get(URL)).json()["prefill"]
    assert [c["field"] for c in prefill["changes"]] == ["custom_alerts"]
    assert prefill["needs_health_consent"] is False


async def test_prefill_set_active_response_has_prefill(client, login):
    login(A)
    await client.put(URL, json={"types": ["gym"], "follow_ups": {"gym_goal": "stay_fit"}})
    r = await client.patch(ACTIVE, json={"active_type": "gym"})
    assert [c["field"] for c in r.json()["prefill"]["changes"]] == ["goal"]

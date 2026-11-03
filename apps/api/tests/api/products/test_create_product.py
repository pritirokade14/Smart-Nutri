"""Plan 4 Task 5: POST /v1/products from a confirmed label draft or a manual entry.

Health-critical: saved values feed verdicts. Covers the confidence rule (label drafts keep
the extraction confidence, manual entry is 1.0), plausibility (the engine's sanitized()),
Devanagari ingredients end to end, Ruling R14 (a value the draft withholds from the engine
is saved only when the user confirmed it) and Ruling R6 / CROSS-PLAN 18 (pending products
are visible only to their creator; the public route serves verified products only).
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me.service import ensure_account
from app.features.members.models import Member
from app.features.products.models import Product
from app.features.products.off_mapping import split_ingredients
from app.features.products.service import record_to_product
from app.features.scans.models import Scan
from app.features.scans.normalize import to_draft
from app.features.scans.schemas import NutrientsIn, NutritionExtraction
from app.integrations.openfoodfacts import get_off_client
from tests.api.analyze.conftest import A, B, today
from tests.api.products.test_lookup_service import FakeOff

URL = "/v1/products"
BARCODE = "8901725181222"
NUTRIENT_FIELDS = (
    "energy_kcal",
    "protein_g",
    "carbs_g",
    "sugars_g",
    "fat_g",
    "sat_fat_g",
    "fiber_g",
    "salt_g",
    "sodium_mg",
)


# --- helpers -----------------------------------------------------------------------------


def nutrients(**kw) -> dict:
    return dict.fromkeys(NUTRIENT_FIELDS) | kw


def body(**kw) -> dict:
    base = {
        "name": "Peanut Chikki",
        "category": "general",
        "basis": "per_100g",
        "nutrients": nutrients(energy_kcal=480, sugars_g=30, carbs_g=60, fat_g=20, protein_g=12),
    }
    return base | kw


def extraction(**kw) -> NutritionExtraction:
    data = {
        "product_name": "Label Snack",
        "brand": "Acme",
        "basis_detected": "per_100g",
        "per_100g": NutrientsIn(**dict.fromkeys(NutrientsIn.model_fields)),
        "per_serving": None,
        "per_100_unit": None,
        "serving_size_g": None,
        "serving_size_unit": None,
        "ingredients": ["sugar"],
        "allergen_statement": None,
        "may_contain_statement": None,
        "claims": [],
        "veg_mark": None,
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
        "upper_bound_fields": [],
    }
    return NutritionExtraction(**(data | kw))


def n_in(**kw) -> NutrientsIn:
    return NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | kw))


def draft_body(draft) -> dict:
    """What a client sends when the user confirms the draft unchanged."""
    return {
        "name": draft.name,
        "brand": draft.brand,
        "category": draft.category,
        "basis": "per_100g",
        "nutrients": {f: getattr(draft.per_100g, f) for f in NUTRIENT_FIELDS},
        "serving_size_g": draft.serving_size_g,
        "ingredients": draft.ingredients,
        "allergen_statement": draft.allergen_statement,
        "may_contain_statement": draft.may_contain_statement,
        "claims": draft.claims,
        "veg_mark": draft.veg_mark,
    }


async def _add(db_session, row):
    db_session.add(row)
    await db_session.flush()
    return row


async def _account(db_session, account_id: UUID) -> None:
    await ensure_account(db_session, AccountContext(account_id, None))


async def _scan(db_session, account_id: UUID, draft) -> Scan:
    """A label scan as Task 4 stores it (the draft contract)."""
    await _account(db_session, account_id)
    return await _add(
        db_session,
        Scan(
            account_id=account_id,
            image_path=f"{account_id}/{uuid4()}.jpg",
            image_sha256=uuid4().hex,
            analysis={
                "draft": draft.model_dump(mode="json"),
                "prompt_version": "extraction_v1",
                "model": "test-vision",
            },
        ),
    )


async def _product(db_session, product_id: str) -> Product:
    return await db_session.scalar(
        select(Product)
        .where(Product.id == UUID(product_id))
        .execution_options(populate_existing=True)
    )


async def _count_products(db_session) -> int:
    return await db_session.scalar(select(func.count()).select_from(Product))


# --- fixtures ----------------------------------------------------------------------------


@pytest.fixture
def fake_off():
    return FakeOff(None)  # OFF knows nothing: only our own catalogue can answer


@pytest.fixture
def login(app, db_session, fake_off):
    def _login(account_id: UUID | None = A):
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[get_off_client] = lambda: fake_off
        if account_id is None:
            app.dependency_overrides.pop(current_account, None)
        else:
            app.dependency_overrides[current_account] = lambda: AccountContext(
                account_id, "asha@example.com"
            )

    return _login


@pytest.fixture
def auth_client(client, login):
    login(A)
    return client


@pytest.fixture
async def scan_with_draft_conf_0_6(db_session):
    return await _scan(db_session, A, to_draft(extraction(confidence=0.6)))


@pytest.fixture
async def other_account_scan(db_session):
    return await _scan(db_session, B, to_draft(extraction()))


@pytest.fixture
async def seeded_product(db_session):
    return await _add(
        db_session,
        Product(
            barcode=BARCODE,
            name="Own Biscuit",
            source="label",
            verification_status="verified",
            category="general",
            per_100g={"sugars_g": 12.5},
            claims=[],
        ),
    )


async def _member(db_session, account_id: UUID = A, **kw) -> Member:
    await _account(db_session, account_id)
    data = {
        "account_id": account_id,
        "name": "Ravi",
        "relation": "self",
        "birth_year": today().year - 35,
        "diet": "non_veg",
        "allergens": [],
        "conditions": [],
    }
    return await _add(db_session, Member(**(data | kw)))


@pytest.fixture
async def peanut_allergic_member(db_session):
    return await _member(db_session, allergens=["peanut"])


@pytest.fixture
async def weight_loss_member(db_session):
    return await _member(db_session, name="Meera", goal="weight_loss")


async def create(client, **kw):
    return await client.post(URL, json=body(**kw))


async def analyze(client, product_id: str, member: Member):
    return await client.post(
        "/v1/analyze", json={"product_id": product_id, "member_ids": [str(member.id)]}
    )


# --- auth and validation -----------------------------------------------------------------


async def test_requires_auth(client, login):
    login(None)
    r = await client.post(URL, json=body())
    assert r.status_code == 401


@pytest.mark.parametrize(
    "bad",
    [
        {"name": "   "},
        {"nutrients": None},
        {"basis": "per_kg"},
        {"sodium_unit": "kg"},
        {"confirmed_fields": ["serving"]},
        {"category": "snack"},
        {"veg_mark": "green"},
    ],
)
async def test_bad_input_is_validation_error(auth_client, db_session, bad):
    before = await _count_products(db_session)
    r = await auth_client.post(URL, json=body() | bad)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert await _count_products(db_session) == before


# --- the plan's tests --------------------------------------------------------------------


async def test_create_from_scan_keeps_extraction_confidence(
    auth_client, db_session, scan_with_draft_conf_0_6
):
    scan = scan_with_draft_conf_0_6
    # The user edited ingredients and allergens: their edits must not raise the confidence.
    r = await create(
        auth_client,
        scan_id=str(scan.id),
        ingredients=["peanuts"],
        allergen_statement="Contains: peanuts",
    )
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["source"] == "smartnutri" and out["attribution"] is None
    rec = await _product(db_session, out["product_id"])
    assert rec.extraction_confidence == 0.6
    assert rec.source == "label" and rec.verification_status == "pending"
    assert rec.created_by == A
    await db_session.refresh(scan)
    assert scan.product_id == rec.id


async def test_manual_entry_confidence_one(auth_client, db_session):
    r = await create(auth_client, ingredients=["sugar"])
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.extraction_confidence == 1.0
    assert rec.source == "user" and rec.verification_status == "pending"
    assert rec.created_by == A


async def test_low_confidence_product_gives_unknown_for_allergic(
    auth_client, scan_with_draft_conf_0_6, peanut_allergic_member
):
    r = await create(auth_client, scan_id=str(scan_with_draft_conf_0_6.id), ingredients=["sugar"])
    v = (await analyze(auth_client, r.json()["product_id"], peanut_allergic_member)).json()
    assert v["verdicts"][0]["status"] == "unknown"


async def test_implausible_rejected(auth_client, db_session):
    before = await _count_products(db_session)
    r = await create(auth_client, nutrients=nutrients(sugars_g=250, carbs_g=60))
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "implausible_value" and err["message_key"] == "error.implausible_value"
    assert err["details"] == {"field": "sugars_g", "fields": ["sugars_g"]}
    assert await _count_products(db_session) == before


@pytest.mark.parametrize(
    ("kw", "fields"),
    [
        ({"nutrients": nutrients(sugars_g=40, carbs_g=20)}, ["carbs_g", "sugars_g"]),
        ({"nutrients": nutrients(sodium_mg=-5)}, ["sodium_mg"]),
        ({"nutrients": nutrients(energy_kcal=5000)}, ["energy_kcal"]),
        (
            {"nutrients": nutrients(protein_g=50, carbs_g=40, fat_g=30)},
            ["protein_g", "carbs_g", "fat_g"],
        ),
        ({"serving_size_g": 0}, ["serving_size_g"]),
        ({"nutrients": nutrients(fat_g=101), "serving_size_g": -1}, ["fat_g", "serving_size_g"]),
    ],
)
async def test_implausible_uses_engine_sanitized(auth_client, kw, fields):
    r = await create(auth_client, **kw)
    assert r.status_code == 422
    assert r.json()["error"]["details"] == {"field": fields[0], "fields": fields}


async def test_blank_values_stay_none(auth_client, db_session):
    r = await create(
        auth_client,
        nutrients=nutrients(sugars_g=12),
        ingredients=["  ", ""],
        allergen_statement="   ",
        brand=" ",
    )
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["per_100g"] == nutrients(sugars_g=12)  # never 0
    rec = await _product(db_session, out["product_id"])
    assert rec.per_100g == nutrients(sugars_g=12) | {"added_sugars_g": None, "trans_fat_g": None}
    assert rec.ingredients_text is None and rec.allergen_statement is None
    assert rec.brand is None and rec.serving_size_g is None


async def test_fields_are_stored(auth_client, db_session):
    r = await create(
        auth_client,
        name="  Masala Chaas ",
        brand="Amul",
        category="beverage",
        nutrients=nutrients(energy_kcal=20, sugars_g=1, carbs_g=2, salt_g=0.4),
        serving_size_g=200,
        ingredients=[" Milk solids ", "Salt", "जीरा"],
        allergen_statement="Contains: milk",
        may_contain_statement="May contain: nuts",
        claims=["low fat"],
        veg_mark="veg",
    )
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["name"] == "Masala Chaas" and out["brand"] == "Amul"
    assert out["category"] == "beverage" and out["serving_size_g"] == 200
    assert out["ingredients"] == ["Milk solids", "Salt", "जीरा"]
    assert out["claims"] == ["low fat"] and out["barcode"] is None
    rec = await _product(db_session, out["product_id"])
    assert rec.ingredients_text == "Milk solids, Salt, जीरा"
    assert rec.may_contain_statement == "May contain: nuts" and rec.veg_mark == "veg"


async def test_duplicate_barcode_conflict(auth_client, db_session, seeded_product):
    before = await _count_products(db_session)
    r = await create(auth_client, barcode="8901725-181222")  # normalised before the check
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "product_exists"
    assert err["details"] == {"product_id": str(seeded_product.id)}
    assert await _count_products(db_session) == before


async def test_own_pending_barcode_conflict(auth_client, db_session):
    first = await create(auth_client, barcode=BARCODE)
    assert first.status_code == 201
    r = await create(auth_client, barcode=BARCODE)
    assert r.status_code == 409
    assert r.json()["error"]["details"] == {"product_id": first.json()["product_id"]}


async def test_barcode_is_normalised_and_stored(auth_client, db_session):
    r = await create(auth_client, barcode=" 8901725 181222 ")
    assert r.status_code == 201 and r.json()["barcode"] == BARCODE


async def test_invalid_barcode(auth_client):
    r = await create(auth_client, barcode="abc")
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_barcode"


async def test_foreign_scan_404(auth_client, db_session, other_account_scan):
    before = await _count_products(db_session)
    foreign = await create(auth_client, scan_id=str(other_account_scan.id))
    unknown = await create(auth_client, scan_id=str(uuid4()))
    assert foreign.status_code == unknown.status_code == 404
    assert foreign.json() == unknown.json()  # no existence leak
    assert foreign.json()["error"]["code"] == "scan_not_found"
    assert await _count_products(db_session) == before


async def test_scan_without_draft_is_not_found(auth_client, db_session):
    await _account(db_session, A)
    barcode_scan = await _add(db_session, Scan(account_id=A, analysis={"verdicts": []}))
    r = await create(auth_client, scan_id=str(barcode_scan.id))
    assert r.status_code == 404 and r.json()["error"]["code"] == "scan_not_found"


async def test_scan_saved_twice_returns_the_first_product(
    auth_client, db_session, scan_with_draft_conf_0_6
):
    scan_id = str(scan_with_draft_conf_0_6.id)
    first = await create(auth_client, scan_id=scan_id)
    assert first.status_code == 201
    before = await _count_products(db_session)
    again = await create(auth_client, scan_id=scan_id)  # e.g. a client retry
    assert again.status_code == 409
    assert again.json()["error"]["details"] == {"product_id": first.json()["product_id"]}
    assert await _count_products(db_session) == before


async def test_devanagari_ingredients_reach_engine(auth_client, db_session, peanut_allergic_member):
    r = await create(auth_client, ingredients=["मूंगफली", "नमक"])
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.ingredients_text == "मूंगफली, नमक"
    v = (await analyze(auth_client, r.json()["product_id"], peanut_allergic_member)).json()
    assert v["verdicts"][0]["status"] == "avoid"


# --- Ruling R14: a value the draft withholds is saved only when the user confirmed it -------


def _diet_drink_draft():
    # A diet cola: "<0.1 g protein, <1 kcal" per 100 ml.
    return to_draft(
        extraction(
            product_name="Diet Cola",
            per_100g=n_in(
                energy_kcal=1,
                protein_g=0.1,
                carbs_g=0,
                sugars_g=0,
                fat_g=0,
                sat_fat_g=0,
                salt_g=0.02,
            ),
            per_100_unit="ml",
            category_guess="beverage",
            upper_bound_fields=["per_100g.energy_kcal", "per_100g.protein_g"],
            ingredients=["carbonated water", "colour (INS 150d)", "sweetener (INS 951)"],
        )
    )


def _codes(analyze_response) -> set[str]:
    return {reason["code"] for reason in analyze_response.json()["verdicts"][0]["reasons"]}


async def test_diet_drink_saved_without_confirming_protein(
    auth_client, db_session, weight_loss_member
):
    draft = _diet_drink_draft()
    assert draft.positive_suppressed == ["protein_g"]
    scan = await _scan(db_session, A, draft)
    r = await auth_client.post(URL, json=draft_body(draft) | {"scan_id": str(scan.id)})
    assert r.status_code == 201, r.text
    assert r.json()["per_100g"]["protein_g"] is None
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["protein_g"] is None
    assert rec.per_100g["energy_kcal"] == 1  # only withheld fields are cleared
    v = await analyze(auth_client, r.json()["product_id"], weight_loss_member)
    assert "good_protein_density" not in _codes(v)


async def test_diet_drink_with_protein_confirmed_is_stored(
    auth_client, db_session, weight_loss_member
):
    draft = _diet_drink_draft()
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id), "confirmed_fields": ["protein_g"]}
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["protein_g"] == 0.1
    # Control: the confirmed value does reach the engine (so the test above tests R14).
    v = await analyze(auth_client, r.json()["product_id"], weight_loss_member)
    assert "good_protein_density" in _codes(v)


async def test_edited_but_unconfirmed_withheld_value_is_not_saved(auth_client, db_session):
    draft = _diet_drink_draft()
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id)}
    payload["nutrients"] = payload["nutrients"] | {"protein_g": 0.3}
    r = await auth_client.post(URL, json=payload)
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["protein_g"] is None

    payload |= {"confirmed_fields": ["protein_g"]}
    scan2 = await _scan(db_session, A, draft)
    r = await auth_client.post(URL, json=payload | {"scan_id": str(scan2.id)})
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["protein_g"] == 0.3  # confirmed: stored as typed


async def test_confirmed_fields_do_not_matter_for_fields_the_draft_did_not_withhold(
    auth_client, db_session
):
    draft = _diet_drink_draft()
    scan = await _scan(db_session, A, draft)
    r = await auth_client.post(URL, json=draft_body(draft) | {"scan_id": str(scan.id)})
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["salt_g"] == 0.02 and rec.per_100g["sugars_g"] == 0


async def test_manual_entry_is_taken_as_typed(auth_client, db_session, weight_loss_member):
    # A person typed every value, so nothing is withheld (no draft, no confirmed_fields).
    draft = _diet_drink_draft()
    r = await auth_client.post(URL, json=draft_body(draft))
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["protein_g"] == 0.1


async def test_unknown_confirmed_field_is_rejected(auth_client):
    r = await create(auth_client, confirmed_fields=["added_sugars_g"])
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


@pytest.fixture
def r13_draft():
    """The real ProductDraft: Ruling R13's engine_withheld is part of normalize.py."""
    from app.features.scans.normalize import ProductDraft

    return ProductDraft


async def _sodium_unit_unconfirmed_scan(db_session, r13_draft):
    # Sodium printed with no unit: the draft keeps it as mg but withholds it from the engine.
    draft = to_draft(
        extraction(per_100g=n_in(energy_kcal=400, sodium_mg=600, sugars_g=5, carbs_g=60))
    )
    assert "unit_unconfirmed:per_100g.sodium_mg" in draft.warnings
    assert draft.engine_withheld == ["sodium_mg"]
    return await _scan(db_session, A, draft), draft


async def test_withheld_sodium_left_blank_gives_hypertensive_unknown(
    auth_client, db_session, r13_draft
):
    # The user could not confirm the unit and blanked sodium: nothing to convert, nothing stored.
    member = await _member(db_session, name="Dadi", conditions=["hypertension"])
    scan, draft = await _sodium_unit_unconfirmed_scan(db_session, r13_draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id)}
    payload["nutrients"] = payload["nutrients"] | {"sodium_mg": None}
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["sodium_mg"] is None and rec.per_100g["salt_g"] is None
    v = (await analyze(auth_client, r.json()["product_id"], member)).json()["verdicts"][0]
    assert v["status"] == "unknown"
    assert any(
        reason["code"] == "nutrient_missing" and reason["params"]["rule"] == "hypertension"
        for reason in v["reasons"]
    )


async def test_withheld_sodium_with_explicit_unit_is_stored(auth_client, db_session, r13_draft):
    # R17: picking the unit is the confirmation; the server does the arithmetic.
    scan, draft = await _sodium_unit_unconfirmed_scan(db_session, r13_draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id), "sodium_unit": "mg"}
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["sodium_mg"] == 600


async def test_withheld_sodium_confirmed_without_a_unit_is_rejected(
    auth_client, db_session, r13_draft
):
    # R17: confirming the value is not enough; the unit must be chosen explicitly.
    scan, draft = await _sodium_unit_unconfirmed_scan(db_session, r13_draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id), "confirmed_fields": ["sodium_mg"]}
    before = await _count_products(db_session)
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 422, r.text
    assert r.json()["error"] == {
        "code": "validation_error",
        "message_key": "error.validation_error",
        "details": {"fields": ["body.sodium_unit"]},
    }
    assert await _count_products(db_session) == before


async def test_confidence_comes_from_the_scan_never_the_body(
    auth_client, db_session, scan_with_draft_conf_0_6
):
    r = await create(
        auth_client,
        scan_id=str(scan_with_draft_conf_0_6.id),
        extraction_confidence=1.0,
        confidence=1.0,
        source="user",
        verification_status="verified",
    )
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.extraction_confidence == 0.6
    assert rec.source == "label" and rec.verification_status == "pending"


# --- ingredients and statements keep their text --------------------------------------------


@pytest.mark.parametrize(
    ("sent", "items"),
    [
        (["मूंगफली", "नमक"], ["मूंगफली", "नमक"]),
        (
            ["Wheat flour (atta)", "Peanuts (मूंगफली)", "गेहूं का आटा", "Emulsifier (322, 471)"],
            ["Wheat flour (atta)", "Peanuts (मूंगफली)", "गेहूं का आटा", "Emulsifier (322, 471)"],
        ),
        # An item with a top-level separator becomes the items the engine will read.
        (["Salt, iodised", "Sugar; jaggery"], ["Salt", "iodised", "Sugar", "jaggery"]),
    ],
)
async def test_ingredients_round_trip_through_the_engine_splitter(
    auth_client, db_session, sent, items
):
    r = await create(auth_client, ingredients=sent)
    assert r.status_code == 201, r.text
    assert r.json()["ingredients"] == items
    rec = await _product(db_session, r.json()["product_id"])
    assert list(split_ingredients(rec.ingredients_text)) == items
    assert list(record_to_product(rec).ingredients) == items


async def test_unbalanced_brackets_that_would_merge_items_are_rejected(auth_client, db_session):
    before = await _count_products(db_session)
    r = await create(auth_client, ingredients=["Sugar (cane", "Peanuts"])
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error" and err["details"] == {"fields": ["body.ingredients"]}
    assert await _count_products(db_session) == before


async def test_statements_stored_verbatim(auth_client, db_session):
    allergen = "Contains: milk, peanuts | इसमें दूध, मूंगफली है"
    may = "May contain: tree nuts | Made in a facility that also processes sesame"
    r = await create(auth_client, allergen_statement=allergen, may_contain_statement=may)
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.allergen_statement == allergen and rec.may_contain_statement == may


# --- Ruling R6 / CROSS-PLAN 18: pending products are not served to others -----------------


async def test_pending_product_visible_only_to_its_creator(client, login, db_session):
    login(A)
    r = await create(client, barcode=BARCODE)
    assert r.status_code == 201
    pid = r.json()["product_id"]

    own = await client.get(f"/v1/products/barcode/{BARCODE}")
    assert own.status_code == 200 and own.json()["product_id"] == pid

    login(B)
    other = await client.get(f"/v1/products/barcode/{BARCODE}")
    assert other.status_code == 404 and other.json()["error"]["code"] == "product_not_found"
    member = await _member(db_session, B, name="Other")
    by_id = await analyze(client, pid, member)
    assert by_id.status_code == 404 and by_id.json()["error"]["code"] == "product_not_found"


async def test_public_route_serves_verified_products_only(client, login, db_session):
    login(A)
    r = await create(client, barcode=BARCODE)
    assert r.status_code == 201
    login(None)
    public = await client.get(f"/v1/products/{BARCODE}/public")
    assert public.status_code == 404

    rec = await _product(db_session, r.json()["product_id"])
    rec.verification_status = "verified"
    await db_session.flush()
    public = await client.get(f"/v1/products/{BARCODE}/public")
    assert public.status_code == 200
    assert public.json()["product"]["product_id"] == r.json()["product_id"]


async def test_barcode_held_by_another_accounts_pending_product(client, login, db_session):
    # B can't see A's pending product, so B's own confirmed label is saved (without the
    # barcode, which A's row holds) instead of a 409 B could not act on.
    login(A)
    a = await create(client, barcode=BARCODE)
    assert a.status_code == 201
    login(B)
    b = await create(client, barcode=BARCODE, name="B's label")
    assert b.status_code == 201, b.text
    assert b.json()["product_id"] != a.json()["product_id"]
    assert b.json()["barcode"] is None
    assert a.json()["product_id"] not in b.text  # A's product id is not leaked
    rec = await _product(db_session, b.json()["product_id"])
    assert rec.created_by == B and rec.barcode is None


# --- R15: product_creates rate limit ----------------------------------------------------------


async def test_product_create_rate_limited_writes_no_row(app, auth_client, db_session):
    app.state.settings.rate_limit_product_creates_per_day = 2
    for i in range(2):
        assert (await create(auth_client, name=f"Snack {i}")).status_code == 201
    before = await _count_products(db_session)
    r = await create(auth_client, name="Snack 3")
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
    assert await _count_products(db_session) == before


# --- Rulings R16/R17: the server does all nutrient arithmetic --------------------------------


def _verdict(analyze_response) -> str:
    return analyze_response.json()["verdicts"][0]["status"]


def _engine_values(rec) -> dict:
    return {f: rec.per_100g[f] for f in NUTRIENT_FIELDS}


@pytest.fixture
async def diabetic_member(db_session):
    return await _member(db_session, name="Papa", conditions=["diabetes"])


@pytest.fixture
async def hypertensive_member(db_session):
    return await _member(db_session, name="Dadi", conditions=["hypertension"])


# Probe 1 (B1): the category is never defaulted.


def _cola_draft():
    return to_draft(
        extraction(
            product_name="Cola",
            per_100g=n_in(energy_kcal=44, protein_g=0, carbs_g=10.6, sugars_g=10.6, fat_g=0),
            per_100_unit="ml",
            category_guess="beverage",
            ingredients=["carbonated water", "sugar"],
        )
    )


async def test_scan_save_without_category_is_rejected(auth_client, db_session):
    draft = _cola_draft()
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id)}
    del payload["category"]
    before = await _count_products(db_session)
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 422, r.text
    err = r.json()["error"]
    assert err["code"] == "validation_error" and err["details"]["fields"] == ["body.category"]
    assert await _count_products(db_session) == before


async def test_manual_entry_without_category_or_basis_is_rejected(auth_client):
    for missing in ("category", "basis"):
        payload = body()
        del payload[missing]
        r = await auth_client.post(URL, json=payload)
        assert r.status_code == 422, r.text
        assert r.json()["error"]["details"]["fields"] == [f"body.{missing}"]


async def test_cola_saved_as_beverage_gives_diabetic_avoid(
    auth_client, db_session, diabetic_member
):
    draft = _cola_draft()
    scan = await _scan(db_session, A, draft)
    r = await auth_client.post(URL, json=draft_body(draft) | {"scan_id": str(scan.id)})
    assert r.status_code == 201, r.text
    assert r.json()["category"] == "beverage"
    assert _verdict(await analyze(auth_client, r.json()["product_id"], diabetic_member)) == "avoid"


# Probe 2 (B2): sodium printed with no unit; the server converts g -> mg.


def _unitless_sodium_draft():
    draft = to_draft(
        extraction(per_100g=n_in(energy_kcal=400, carbs_g=60, sugars_g=5, sodium_mg=0.4))
    )
    assert "unit_unconfirmed:per_100g.sodium_mg" in draft.warnings
    assert draft.per_100g.sodium_mg == 0.4  # the number as printed
    return draft


async def test_unitless_sodium_in_grams_is_converted_by_the_server(
    auth_client, db_session, hypertensive_member
):
    draft = _unitless_sodium_draft()
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id), "sodium_unit": "g"}
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["sodium_mg"] == 400
    assert r.json()["per_100g"]["sodium_mg"] == 400
    v = await analyze(auth_client, r.json()["product_id"], hypertensive_member)
    assert _verdict(v) != "ok"


async def test_unitless_sodium_without_explicit_unit_is_rejected(auth_client, db_session):
    draft = _unitless_sodium_draft()
    scan = await _scan(db_session, A, draft)
    before = await _count_products(db_session)
    r = await auth_client.post(URL, json=draft_body(draft) | {"scan_id": str(scan.id)})
    assert r.status_code == 422, r.text
    err = r.json()["error"]
    assert err["code"] == "validation_error" and err["details"] == {"fields": ["body.sodium_unit"]}
    assert await _count_products(db_session) == before


async def test_unitless_sodium_with_null_unit_is_rejected(auth_client, db_session):
    # Generated clients serialise every field; a null unit is not a choice.
    draft = _unitless_sodium_draft()
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id), "sodium_unit": None}
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 422, r.text
    assert r.json()["error"]["details"] == {"fields": ["body.sodium_unit"]}


async def test_sodium_unit_has_no_non_null_default_in_the_contract(app):
    # A default of "mg" would be sent by generated clients and look like a user choice.
    schema = app.openapi()["components"]["schemas"]["ProductCreate"]["properties"]
    assert schema["sodium_unit"].get("default") is None


async def test_manual_entry_sodium_unit(auth_client, db_session):
    grams = await create(auth_client, nutrients=nutrients(sodium_mg=0.4), sodium_unit="g")
    default = await create(auth_client, name="Other", nutrients=nutrients(sodium_mg=400))
    assert grams.status_code == default.status_code == 201
    assert (await _product(db_session, grams.json()["product_id"])).per_100g["sodium_mg"] == 400
    assert (await _product(db_session, default.json()["product_id"])).per_100g["sodium_mg"] == 400


async def test_sodium_in_grams_is_plausibility_checked_after_conversion(auth_client):
    r = await create(auth_client, nutrients=nutrients(sodium_mg=400), sodium_unit="g")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "implausible_value"
    assert r.json()["error"]["details"]["fields"] == ["sodium_mg"]


# Probe 3: the x10 serving misread (serving read as 300 g, really 30 g).


def _serving_only_draft():
    draft = to_draft(
        extraction(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n_in(energy_kcal=120, protein_g=2, carbs_g=20, sugars_g=9, fat_g=4),
            serving_size_g=300,
            serving_size_unit="g",
        )
    )
    assert draft.derived_from_serving and draft.per_100g.sugars_g == 3
    assert draft.per_serving is not None and draft.per_serving.sugars_g == 9
    return draft


def _serving_body(draft, **kw) -> dict:
    """What a client sends when the user transcribes the printed per-serving column."""
    return (
        draft_body(draft)
        | {
            "basis": "per_serving",
            "nutrients": {f: getattr(draft.per_serving, f) for f in NUTRIENT_FIELDS},
            "serving_size_g": draft.serving_size_g,
        }
        | kw
    )


async def test_per_serving_save_without_serving_confirmation_stores_nothing(
    auth_client, db_session, diabetic_member
):
    draft = _serving_only_draft()
    scan = await _scan(db_session, A, draft)
    r = await auth_client.post(URL, json=_serving_body(draft, scan_id=str(scan.id)))
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert _engine_values(rec) == nutrients()
    v = await analyze(auth_client, r.json()["product_id"], diabetic_member)
    assert _verdict(v) == "unknown"


async def test_derived_values_saved_as_per_100g_still_need_serving_confirmation(
    auth_client, db_session, diabetic_member
):
    # A client that sends the server-derived per-100 g column cannot skip the serving check.
    draft = _serving_only_draft()
    scan = await _scan(db_session, A, draft)
    r = await auth_client.post(URL, json=draft_body(draft) | {"scan_id": str(scan.id)})
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert _engine_values(rec) == nutrients()
    v = await analyze(auth_client, r.json()["product_id"], diabetic_member)
    assert _verdict(v) == "unknown"


async def test_per_serving_save_with_corrected_serving_is_converted(
    auth_client, db_session, diabetic_member
):
    draft = _serving_only_draft()
    scan = await _scan(db_session, A, draft)
    payload = _serving_body(
        draft, scan_id=str(scan.id), serving_size_g=30, confirmed_fields=["serving_size_g"]
    )
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["sugars_g"] == 30 and rec.per_100g["carbs_g"] == 20 * 100 / 30
    assert rec.per_100g["energy_kcal"] == 400 and rec.serving_size_g == 30
    v = await analyze(auth_client, r.json()["product_id"], diabetic_member)
    assert _verdict(v) == "avoid"


async def test_manual_per_serving_entry_is_converted(auth_client, db_session):
    r = await create(
        auth_client,
        basis="per_serving",
        serving_size_g=50,
        nutrients=nutrients(sugars_g=10, carbs_g=20, sodium_mg=0.1),
        sodium_unit="g",
    )
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["sugars_g"] == 20 and rec.per_100g["carbs_g"] == 40
    assert rec.per_100g["sodium_mg"] == 200  # g -> mg, then per serving -> per 100 g


async def test_per_serving_basis_requires_a_serving_size(auth_client, db_session):
    before = await _count_products(db_session)
    r = await create(auth_client, basis="per_serving", serving_size_g=None)
    assert r.status_code == 422, r.text
    assert r.json()["error"] == {
        "code": "validation_error",
        "message_key": "error.validation_error",
        "details": {"fields": ["body.serving_size_g"]},
    }
    assert await _count_products(db_session) == before


@pytest.mark.parametrize("serving", [0, -5, 5001])
async def test_per_serving_basis_with_implausible_serving_is_rejected(auth_client, serving):
    r = await create(auth_client, basis="per_serving", serving_size_g=serving)
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "implausible_value"
    assert r.json()["error"]["details"]["fields"] == ["serving_size_g"]


async def test_per_serving_values_are_plausibility_checked_after_conversion(auth_client):
    # 40 g sugars in a 30 g serving is 133 g per 100 g.
    r = await create(
        auth_client,
        basis="per_serving",
        serving_size_g=30,
        nutrients=nutrients(sugars_g=40, carbs_g=40),
    )
    assert r.status_code == 422
    assert "sugars_g" in r.json()["error"]["details"]["fields"]


async def test_display_only_values_are_converted_and_stored(auth_client, db_session):
    r = await create(
        auth_client,
        basis="per_serving",
        serving_size_g=25,
        nutrients=nutrients(sugars_g=5, carbs_g=10, fat_g=2)
        | {"added_sugars_g": 4, "trans_fat_g": 0.1},
    )
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["added_sugars_g"] == 16 and rec.per_100g["trans_fat_g"] == 0.4


async def test_display_only_values_are_plausibility_checked(auth_client):
    r = await create(auth_client, nutrients=nutrients(sugars_g=5) | {"added_sugars_g": 30})
    assert r.status_code == 422
    assert r.json()["error"]["details"]["fields"] == ["added_sugars_g"]


# Probe 4: basis mismatch.


def _basis_mismatch_draft():
    # The model said "per serving" but filled only the per-100 g column.
    draft = to_draft(
        extraction(
            basis_detected="per_serving",
            per_100g=n_in(energy_kcal=150, carbs_g=20, sugars_g=10),
        )
    )
    assert "basis_mismatch" in draft.warnings
    return draft


async def test_basis_mismatch_without_basis_is_rejected(auth_client, db_session):
    draft = _basis_mismatch_draft()
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id)}
    del payload["basis"]
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 422, r.text
    assert r.json()["error"]["details"]["fields"] == ["body.basis"]


async def test_basis_mismatch_per_serving_with_confirmed_serving_is_converted(
    auth_client, db_session
):
    draft = _basis_mismatch_draft()
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {
        "scan_id": str(scan.id),
        "basis": "per_serving",
        "serving_size_g": 25,
        "confirmed_fields": ["serving_size_g"],
    }
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["sugars_g"] == 40 and rec.per_100g["carbs_g"] == 80
    assert rec.per_100g["energy_kcal"] == 600


async def test_basis_mismatch_explicit_per_100g_confirms_the_values(auth_client, db_session):
    draft = _basis_mismatch_draft()
    scan = await _scan(db_session, A, draft)
    r = await auth_client.post(URL, json=draft_body(draft) | {"scan_id": str(scan.id)})
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["sugars_g"] == 10 and rec.per_100g["energy_kcal"] == 150


async def test_basis_mismatch_explicit_basis_keeps_upper_bound_protein_withheld(
    auth_client, db_session
):
    draft = to_draft(
        extraction(
            basis_detected="per_serving",
            per_100g=n_in(energy_kcal=20, protein_g=0.5, carbs_g=4, sugars_g=4),
            upper_bound_fields=["per_100g.protein_g"],
        )
    )
    assert "basis_mismatch" in draft.warnings
    scan = await _scan(db_session, A, draft)
    r = await auth_client.post(URL, json=draft_body(draft) | {"scan_id": str(scan.id)})
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["protein_g"] is None and rec.per_100g["sugars_g"] == 4


# Probe 7: only the barcode constraint is a product_exists conflict.


async def test_concurrent_barcode_save_is_conflict_with_product_id(
    auth_client, db_session, seeded_product, monkeypatch
):
    from app.features.products import service as products_service

    original = products_service._barcode_for_new_product
    calls = {"n": 0}

    async def racing(session, account_id, barcode):
        calls["n"] += 1
        if calls["n"] == 1:  # the check ran before the other save committed
            return barcode
        return await original(session, account_id, barcode)

    monkeypatch.setattr(products_service, "_barcode_for_new_product", racing)
    before = await _count_products(db_session)
    r = await create(auth_client, barcode=BARCODE)
    assert r.status_code == 409, r.text
    err = r.json()["error"]
    assert err["code"] == "product_exists"
    assert err["details"] == {"product_id": str(seeded_product.id)}
    assert await _count_products(db_session) == before


async def test_concurrent_save_by_an_invisible_holder_saves_without_barcode(
    auth_client, db_session, monkeypatch
):
    from app.features.products import service as products_service

    await _account(db_session, B)
    other = await _add(
        db_session,
        Product(
            barcode=BARCODE,
            name="B's pending",
            source="label",
            verification_status="pending",
            created_by=B,
            category="general",
            per_100g={},
            claims=[],
        ),
    )
    original = products_service._barcode_for_new_product
    calls = {"n": 0}

    async def racing(session, account_id, barcode):
        calls["n"] += 1
        if calls["n"] == 1:
            return barcode
        return await original(session, account_id, barcode)

    monkeypatch.setattr(products_service, "_barcode_for_new_product", racing)
    r = await create(auth_client, barcode=BARCODE)
    assert r.status_code == 201, r.text
    assert r.json()["barcode"] is None and str(other.id) not in r.text


async def test_other_integrity_errors_are_not_product_exists(auth_client, db_session, monkeypatch):
    from app.features.products import service as products_service

    monkeypatch.setattr(products_service, "MANUAL_ENTRY_CONFIDENCE", 2.0)  # violates a CHECK
    before = await _count_products(db_session)
    r = await create(auth_client)
    assert r.status_code == 500, r.text
    assert r.json()["error"]["code"] != "product_exists"
    assert await _count_products(db_session) == before


# Probe 8: plausibility checks only the values that will be stored.


async def test_unconfirmed_withheld_implausible_value_is_not_checked(auth_client, db_session):
    draft = to_draft(
        extraction(per_100g=n_in(energy_kcal=400, fat_g=5, sat_fat_g=2, carbs_g=60))
    ).model_copy(update={"engine_withheld": ["sat_fat_g"]})
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id)}
    payload["nutrients"] = payload["nutrients"] | {"sat_fat_g": 20}  # > fat_g
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.per_100g["sat_fat_g"] is None and rec.per_100g["fat_g"] == 5

    # Confirmed, the same value is stored, so it is checked.
    scan2 = await _scan(db_session, A, draft)
    payload |= {"scan_id": str(scan2.id), "confirmed_fields": ["sat_fat_g"]}
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 422 and r.json()["error"]["code"] == "implausible_value"


# Probe 10: length caps match what labels print; nothing is truncated.


async def test_long_ingredient_lists_and_statements_are_accepted(auth_client, db_session):
    items = [f"ingredient {i} " + "x" * 980 for i in range(400)]
    assert max(len(i) for i in items) <= 1000
    statement = "Contains: " + "y" * 3990
    assert len(statement) == 4000
    r = await create(
        auth_client,
        ingredients=items,
        allergen_statement=statement,
        may_contain_statement=statement,
    )
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert list(split_ingredients(rec.ingredients_text)) == items
    assert rec.allergen_statement == statement and rec.may_contain_statement == statement


@pytest.mark.parametrize(
    "bad",
    [
        {"ingredients": ["x"] * 401},
        {"ingredients": ["x" * 1001]},
        {"allergen_statement": "y" * 4001},
        {"may_contain_statement": "y" * 4001},
    ],
)
async def test_over_length_input_is_rejected_not_truncated(auth_client, bad):
    r = await create(auth_client, **bad)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


# --- Ruling R18: a scanned serving size is stored only when the user confirmed it ---------


def _misread_serving_draft():
    # The label says 3 g sugars per 100 g, but the serving was misread as 300 g.
    return to_draft(
        extraction(
            product_name="Misread Serving Snack",
            per_100g=n_in(energy_kcal=100, sugars_g=3, carbs_g=20, fat_g=1, protein_g=2),
            serving_size_g=300,
        )
    )


def _child_sugar_params(analyze_response) -> list[dict]:
    reasons = analyze_response.json()["verdicts"][0]["reasons"]
    return [r["params"] for r in reasons if r["code"].startswith("child_sugar")]


async def test_scan_save_with_unconfirmed_serving_stores_none(auth_client, db_session):
    child = await _member(db_session, name="Kid", birth_year=today().year - 6)
    draft = _misread_serving_draft()
    assert draft.serving_size_g == 300
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {"scan_id": str(scan.id)}
    assert payload["serving_size_g"] == 300 and "confirmed_fields" not in payload
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 201, r.text
    assert r.json()["serving_size_g"] is None
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.serving_size_g is None
    v = await analyze(auth_client, r.json()["product_id"], child)
    assert all(p["basis"] == "per_100g" for p in _child_sugar_params(v))


async def test_scan_save_with_confirmed_serving_stores_it(auth_client, db_session):
    child = await _member(db_session, name="Kid", birth_year=today().year - 6)
    draft = _misread_serving_draft()
    scan = await _scan(db_session, A, draft)
    payload = draft_body(draft) | {
        "scan_id": str(scan.id),
        "confirmed_fields": ["serving_size_g"],
    }
    r = await auth_client.post(URL, json=payload)
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.serving_size_g == 300
    # Control: the confirmed serving does reach the engine (so the tests above test R18).
    v = await analyze(auth_client, r.json()["product_id"], child)
    assert [p["basis"] for p in _child_sugar_params(v)] == ["per_serving"]


async def test_manual_entry_serving_is_stored_without_confirmation(auth_client, db_session):
    r = await create(auth_client, serving_size_g=30)
    assert r.status_code == 201, r.text
    rec = await _product(db_session, r.json()["product_id"])
    assert rec.serving_size_g == 30

"""R21: the confirm hints are the save rules (end to end, over every shared draft fixture).

1. Every scripted save in packages/test-fixtures/drafts/expected.json, posted to
   POST /v1/products against a stored label scan, gives exactly the recorded result (the
   status, the 422 code and fields, or the stored row).
2. Property: for every fixture and every offered basis, a body that honours `draft.confirm`
   is stored in full; a body that ignores it is a 422 with the documented field or stores
   null for each hinted field, and never a value the user did not confirm.
"""

import json
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me.service import ensure_account
from app.features.products.models import Product
from app.features.scans.models import Scan
from app.features.scans.normalize import ENGINE_FIELDS, ProductDraft, to_draft
from app.features.scans.schemas import NutritionExtraction
from app.features.scans.service import label_scan_analysis
from scripts.export_draft_fixtures import CASES, DRAFTS, build_body
from tests.api.analyze.conftest import A

URL = "/v1/products"
EXPECTED = json.loads((DRAFTS / "expected.json").read_text(encoding="utf-8"))["cases"]


@pytest.fixture
def auth_client(app, client, db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[current_account] = lambda: AccountContext(A, "asha@example.com")
    return client


async def _label_scan(db_session, extraction: NutritionExtraction) -> Scan:
    """A label scan as POST /v1/scans/label stores it (raw extraction + draft)."""
    await ensure_account(db_session, AccountContext(A, None))
    scan = Scan(
        account_id=A,
        image_path=f"{A}/{uuid4()}.jpg",
        image_sha256=uuid4().hex,
        analysis=label_scan_analysis(
            to_draft(extraction),
            extraction=extraction,
            prompt_version="extraction_v1",
            model="test-vision",
        ),
    )
    db_session.add(scan)
    await db_session.flush()
    return scan


async def _post(client, db_session, name: str, body: dict[str, Any]):
    scan = await _label_scan(db_session, CASES[name].extraction)
    r = await client.post(URL, json=body | {"scan_id": str(scan.id)})
    rec = None
    if r.status_code == 201:
        rec = await db_session.scalar(
            select(Product)
            .where(Product.id == UUID(r.json()["product_id"]))
            .execution_options(populate_existing=True)
        )
    return r, rec


# --- 1. expected.json, end to end --------------------------------------------------------------

SAVES = [
    pytest.param(name, i, id=f"{name}-{i}")
    for name, case in EXPECTED.items()
    for i in range(len(case["saves"]))
]


@pytest.mark.parametrize(("name", "index"), SAVES)
async def test_expected_save_end_to_end(auth_client, db_session, name, index):
    save = EXPECTED[name]["saves"][index]
    expected = save["result"]
    r, rec = await _post(auth_client, db_session, name, save["body"])
    assert r.status_code == expected["status"], r.text
    if expected["status"] != 201:
        error = r.json()["error"]
        assert error["code"] == expected["error"]["code"]
        assert error["details"]["fields"] == expected["error"]["fields"]
        return
    stored = expected["stored"]
    assert rec.per_100g == stored["per_100g"]
    assert rec.serving_size_g == stored["serving_size_g"]
    assert rec.category == stored["category"]
    assert rec.extraction_confidence == stored["extraction_confidence"]


def test_expected_drafts_are_what_the_scan_returns():
    for name in EXPECTED:
        data = json.loads((DRAFTS / EXPECTED[name]["draft"]).read_text(encoding="utf-8"))
        assert to_draft(CASES[name].extraction).model_dump(mode="json") == data


# --- 2. property: honouring the hints stores everything; ignoring them never guesses ----------


def _draft(name: str) -> ProductDraft:
    return to_draft(CASES[name].extraction)


def _offered(draft: ProductDraft) -> list[str]:
    return [b for b in ("per_100g", "per_serving") if getattr(draft.confirm.columns, b)]


def _fix_implausible(draft: ProductDraft) -> dict[str, None]:
    """The user blanks what the draft flags as implausible (not a confirm hint)."""
    prefix = "implausible_value:"
    return {w[len(prefix) :]: None for w in draft.warnings if w.startswith(prefix)}


def _honest(body: dict[str, Any]) -> dict[str, float | None]:
    """The sent values converted like the pack says (sodium unit, then basis)."""
    values = dict(body["nutrients"])
    if values["sodium_mg"] is not None and body.get("sodium_unit") == "g":
        values["sodium_mg"] *= 1000
    if body["basis"] == "per_serving":
        serving = body["serving_size_g"]
        values = {k: None if v is None else v * 100 / serving for k, v in values.items()}
    return values


CASE_BASES = [
    pytest.param(name, basis, id=f"{name}-{basis}")
    for name in sorted(CASES)
    for basis in _offered(_draft(name))
]


@pytest.mark.parametrize(("name", "basis"), CASE_BASES)
async def test_honouring_the_hints_stores_every_value(auth_client, db_session, name, basis):
    draft = _draft(name)
    hints = getattr(draft.confirm.columns, basis)
    actions: dict[str, Any] = {
        "pick_basis": basis,
        "pick_category": draft.category,
        "tick": list(hints.confirm_fields),
        "edit": _fix_implausible(draft),
    }
    if hints.sodium_unit_required:
        actions["sodium_unit"] = "mg"
    body = build_body(draft, actions)
    r, rec = await _post(auth_client, db_session, name, body)
    assert r.status_code == 201, r.text
    assert rec.per_100g == _honest(body)  # nothing the user confirmed was dropped
    assert rec.serving_size_g == body["serving_size_g"]
    assert any(rec.per_100g[f] is not None for f in ENGINE_FIELDS)


@pytest.mark.parametrize(("name", "basis"), CASE_BASES)
async def test_ignoring_the_hints_never_stores_a_guess(auth_client, db_session, name, basis):
    draft = _draft(name)
    hints = getattr(draft.confirm.columns, basis)
    # Ticks and the sodium unit ignored; the basis and category are explicit here (their
    # omission is tested below).
    actions = {
        "pick_basis": basis,
        "pick_category": draft.category,
        "edit": _fix_implausible(draft),
    }
    body = build_body(draft, actions)
    r, rec = await _post(auth_client, db_session, name, body)

    if hints.sodium_unit_required and body["nutrients"]["sodium_mg"] is not None:
        assert r.status_code == 422, r.text
        assert r.json()["error"]["details"]["fields"] == ["body.sodium_unit"]
        return
    assert r.status_code == 201, r.text
    hinted = set(hints.confirm_fields)
    serving_hinted = "serving_size_g" in hinted
    assert rec.serving_size_g == (None if serving_hinted else body["serving_size_g"])
    if all(v is None for v in rec.per_100g.values()):
        # Nothing stored: only allowed when an unticked serving size gates every value.
        assert serving_hinted
        return
    honest = _honest(body)
    for field, value in rec.per_100g.items():
        assert value == (None if field in hinted else honest[field]), field


@pytest.mark.parametrize("name", [n for n in sorted(CASES) if _draft(n).confirm.basis_required])
async def test_no_basis_on_a_mismatch_is_a_422(auth_client, db_session, name):
    body = build_body(_draft(name), {"pick_category": _draft(name).category})
    assert "basis" not in body
    r, rec = await _post(auth_client, db_session, name, body)
    assert r.status_code == 422 and rec is None
    assert r.json()["error"]["details"]["fields"] == ["body.basis"]


@pytest.mark.parametrize("name", [n for n in sorted(CASES) if _draft(n).confirm.category_required])
async def test_no_category_on_a_category_warning_is_a_422(auth_client, db_session, name):
    draft = _draft(name)
    body = build_body(draft, {})
    assert "category" not in body
    r, rec = await _post(auth_client, db_session, name, body)
    assert r.status_code == 422 and rec is None
    assert r.json()["error"]["details"]["fields"] == ["body.category"]

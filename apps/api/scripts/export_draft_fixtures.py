"""Check or regenerate packages/test-fixtures/drafts/ (shared confirm-screen fixtures, R21c).

Run from apps/api:
  uv run python scripts/export_draft_fixtures.py          # --check (default): diff, exit 1 if stale
  uv run python scripts/export_draft_fixtures.py --write  # write only the files that differ

Each case is a raw `NutritionExtraction` (what the vision model returns) fed through the real
normaliser (`to_draft`):
  drafts/<case>.json    the `ProductDraft` exactly as `POST /v1/scans/label` returns it in
                        `draft` (including the server-computed `confirm` hints)
  drafts/expected.json  per case, scripted user actions -> the exact `ProductCreate` body a
                        client must send -> the server's result (stored values or the 422).
                        An edit to a different value counts as a confirmation (R24).
                        `"client_blocks": true` marks every save a client must refuse to send

Results come from `products.service.stored_values`, the function `POST /v1/products` runs;
tests/api/products/test_draft_fixture_saves.py posts every body end to end and checks the
stored row. tests/fixtures/test_draft_fixtures.py fails when the files are stale. Never edit
them by hand. Format: packages/test-fixtures/README.md ("Confirm-screen drafts").
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parents[1]))

from pydantic import ValidationError

from app.core.errors import ApiError
from app.features.products.confirm_rules import CONFIRMABLE_FIELDS
from app.features.products.schemas import ProductCreate
from app.features.products.service import stored_values
from app.features.scans.normalize import DraftNutrients, ProductDraft, to_draft
from app.features.scans.schemas import NutrientsIn, NutritionExtraction
from tests.fixtures.loader import FIXTURES

DRAFTS = FIXTURES / "drafts"
FORMAT_VERSION = 1
NUTRIENT_KEYS: tuple[str, ...] = tuple(DraftNutrients.model_fields)  # 9 engine + 2 display
ACTION_KEYS = frozenset({"pick_basis", "pick_category", "tick", "sodium_unit", "edit"})

# Per 100 g; plausible also when read as per a 30 g serving (x 100/30).
_V = {
    "energy_kcal": 150.0,
    "protein_g": 3.0,
    "carbs_g": 20.0,
    "sugars_g": 10.0,
    "added_sugars_g": 4.0,
    "fat_g": 5.0,
    "sat_fat_g": 2.0,
    "trans_fat_g": 0.1,
    "fiber_g": 1.0,
    "salt_g": 0.5,
    "sodium_mg": 200.0,
    "sodium_unit": "mg",
}
# The same food per 30 g serving.
_S = {k: (round(v * 0.3, 4) if isinstance(v, float) else v) for k, v in _V.items()}


def _n(base: dict[str, Any] | None = None, **kw: Any) -> NutrientsIn:
    return NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | (base or {}) | kw))


def _ex(**kw: Any) -> NutritionExtraction:
    data: dict[str, Any] = {
        "product_name": "Masala Crunch",
        "brand": "Acme Foods",
        "basis_detected": "per_100g",
        "per_100g": _n(_V),
        "per_serving": None,
        "per_100_unit": "g",
        "serving_size_g": None,
        "serving_size_unit": None,
        "ingredients": ["wheat flour", "edible vegetable oil (palm)", "sugar", "salt"],
        "allergen_statement": "Contains wheat",
        "may_contain_statement": "May contain milk",
        "claims": [],
        "veg_mark": "veg",
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
        "upper_bound_fields": [],
    }
    return NutritionExtraction(**(data | kw))


@dataclass(frozen=True)
class Case:
    description: str
    extraction: NutritionExtraction
    saves: list[dict[str, Any]] = field(default_factory=lambda: [{}])


_TICK_SERVING = {"tick": ["serving_size_g"]}

CASES: dict[str, Case] = {
    "clean": Case(
        "Per-100 g label, every unit printed: nothing to ask.",
        _ex(),
    ),
    "basis_mismatch_both_columns": Case(
        "Basis unreadable, both columns printed: the user picks the basis; each column is "
        "shown on its own.",
        _ex(basis_detected="unknown", per_serving=_n(_S), serving_size_g=30),
        [
            {"pick_basis": "per_100g", **_TICK_SERVING},
            {"pick_basis": "per_100g"},
            {"pick_basis": "per_serving", **_TICK_SERVING},
            {"pick_basis": "per_serving"},
            {},
        ],
    ),
    "basis_mismatch_one_column": Case(
        "Label says per serving but only the per-100 g object has values: one shared column, "
        "its basis is the doubt.",
        _ex(basis_detected="per_serving", serving_size_g=30),
        [
            {"pick_basis": "per_100g", **_TICK_SERVING},
            {"pick_basis": "per_serving", **_TICK_SERVING},
            {"pick_basis": "per_serving"},
            {},
        ],
    ),
    "derived_from_serving": Case(
        "Only a per-serving column with a readable serving: per 100 g is derived, so the "
        "serving size must be ticked for anything to be stored.",
        _ex(basis_detected="per_serving", per_100g=None, per_serving=_n(_S), serving_size_g=30),
        [_TICK_SERVING, {}],
    ),
    "per_serving_only_no_serving": Case(
        "Only per-serving values and no readable serving size: only the per-serving column is "
        "offered, never an empty per-100 g one; the user types the serving size and ticks it.",
        _ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=_n(_V, sugars_g=9.0),
            serving_size_g=None,
        ),
        [
            {
                "pick_basis": "per_serving",
                "edit": {"serving_size_g": 30.0, "sugars_g": 9.0},
                **_TICK_SERVING,
            },
            {"pick_basis": "per_serving", "edit": {"serving_size_g": 30.0}},
            {"pick_basis": "per_serving"},
            {},
        ],
    ),
    "derived_basis_mismatch": Case(
        "Label says per 100 g but only per-serving values: derived and in doubt; the "
        "per-serving column is shared.",
        _ex(basis_detected="per_100g", per_100g=None, per_serving=_n(_S), serving_size_g=30),
        [
            {"pick_basis": "per_serving", **_TICK_SERVING},
            {"pick_basis": "per_100g", **_TICK_SERVING},
            {"pick_basis": "per_100g"},
            {},
        ],
    ),
    "unit_unconfirmed_sodium_per_100g": Case(
        'Sodium printed as "0.4" with no unit: the user picks mg or g (no tick).',
        _ex(per_100g=_n(_V, sodium_mg=0.4, sodium_unit=None, salt_g=1.0)),
        [{"sodium_unit": "g"}, {"sodium_unit": "mg"}, {}],
    ),
    "unit_unconfirmed_sodium_per_serving": Case(
        "Unit-less sodium on the per-serving column only: the unit is still required when "
        "saving the per-100 g column (R19).",
        _ex(per_serving=_n(_S, sodium_mg=0.06, sodium_unit=None), serving_size_g=30),
        [
            {"sodium_unit": "mg", **_TICK_SERVING},
            {"sodium_unit": "g", **_TICK_SERVING},
            {"pick_basis": "per_serving", "sodium_unit": "g", **_TICK_SERVING},
            {},
        ],
    ),
    "sodium_unit_suspect": Case(
        'Sodium-only label printing "0.4 g", read as 0.4 mg with no salt to check it: sodium '
        "is withheld and the user picks mg or g (EF2).",
        _ex(per_100g=_n(_V, salt_g=None, sodium_mg=0.4)),
        [{"sodium_unit": "g"}, {"sodium_unit": "mg"}, {}],
    ),
    "upper_bound_protein_per_100g": Case(
        'Protein printed as "<0.5 g": stored only when ticked.',
        _ex(per_100g=_n(_V, protein_g=0.5), upper_bound_fields=["per_100g.protein_g"]),
        [
            {"tick": ["protein_g"]},
            {"edit": {"protein_g": 0.4}},
            {"edit": {"protein_g": 0.5}},  # back to the draft value: confirms nothing (R24)
            {},
        ],
    ),
    "upper_bound_protein_per_serving": Case(
        'Protein "<0.5 g" on the per-serving column: asked whichever column is saved (R19).',
        _ex(
            per_serving=_n(_S, protein_g=0.5),
            serving_size_g=30,
            upper_bound_fields=["per_serving.protein_g"],
        ),
        [
            {"tick": ["protein_g", "serving_size_g"]},
            _TICK_SERVING,
            {"pick_basis": "per_serving", "tick": ["protein_g", "serving_size_g"]},
            {"pick_basis": "per_serving", **_TICK_SERVING},
            {},
        ],
    ),
    "category_check": Case(
        "Printed per 100 ml but the guess was not a drink: the user must pick the category.",
        _ex(
            product_name="Lemon Drink",
            per_100g=_n(
                energy_kcal=44.0,
                protein_g=0.0,
                carbs_g=10.6,
                sugars_g=10.6,
                fat_g=0.0,
                sodium_mg=10.0,
                sodium_unit="mg",
            ),
            per_100_unit="ml",
            ingredients=["water", "sugar", "lemon juice"],
            allergen_statement=None,
            may_contain_statement=None,
        ),
        [{"pick_category": "beverage"}, {}],
    ),
    "category_and_basis": Case(
        "Basis unreadable and a per-100 ml drink the guess did not call a drink: the user must "
        "pick BOTH the basis and the category before a save is sent.",
        _ex(
            product_name="Lemon Drink",
            basis_detected="unknown",
            per_100_unit="ml",
            per_serving=_n(_S),
            serving_size_g=30,
            ingredients=["water", "sugar", "lemon juice"],
            allergen_statement=None,
            may_contain_statement=None,
        ),
        [
            {},
            {"pick_basis": "per_100g"},
            {"pick_category": "beverage"},
            {"pick_basis": "per_100g", "pick_category": "beverage"},
            {"pick_basis": "per_serving", "pick_category": "beverage", **_TICK_SERVING},
        ],
    ),
    "supplement_suggested": Case(
        "Whey protein concentrate listed (P9 safety S5): `confirm.category_suggestion` is "
        '"supplement" and the category must be picked (never preselected); either pick is '
        "saved as is.",
        _ex(
            product_name="Choco Protein Mix",
            ingredients=["whey protein concentrate", "cocoa", "sucralose"],
            allergen_statement="Contains milk",
        ),
        [{"pick_category": "supplement"}, {"pick_category": "general"}, {}],
    ),
    "category_unknown": Case(
        "No category guess: the user must pick the category.",
        _ex(category_guess=None),
        [{"pick_category": "general"}, {}],
    ),
    "low_confidence": Case(
        "Low extraction confidence: no extra question; the stored confidence stays low.",
        _ex(confidence=0.5),
    ),
    "implausible_value": Case(
        "More sugar than carbohydrate: the save is rejected until the user fixes it.",
        _ex(per_100g=_n(_V, sugars_g=40.0)),
        [{}, {"edit": {"sugars_g": 10.0}}],
    ),
    "energy_decimal_shift": Case(
        "Fat read as 50 instead of 5.0: energy disagrees with the macros, fat is named as a "
        "likely decimal slip, and every field in the energy check needs a tick (label v2).",
        _ex(per_100g=_n(_V, fat_g=50.0)),
        [
            {"tick": ["energy_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g"]},
            {"edit": {"fat_g": 5.0}, "tick": ["energy_kcal", "protein_g", "carbs_g", "fiber_g"]},
            {},
        ],
    ),
    "decimal_shift_tight": Case(
        "Protein 3.0 read as 0.3: energy is still within the loose tolerance, but protein x 10 "
        "fits exactly, so protein alone is named and withheld until ticked or fixed (EF3).",
        _ex(per_100g=_n(_V, energy_kcal=137.0, protein_g=0.3)),
        [{"tick": ["protein_g"]}, {"edit": {"protein_g": 3.0}}, {}],
    ),
    "salt_sodium_mismatch": Case(
        "Salt read as 5.0 next to sodium 200 mg: both are withheld until ticked (label v2).",
        _ex(per_100g=_n(_V, salt_g=5.0)),
        [{"tick": ["salt_g", "sodium_mg"]}, {"edit": {"salt_g": 0.5}, "tick": ["sodium_mg"]}, {}],
    ),
    "column_mismatch": Case(
        "Per-serving sugars 6 g where 30 g of a 10 g/100 g food gives 3 g: the columns "
        "disagree, so sugars is withheld whichever column is saved (label v2).",
        _ex(basis_detected="both", per_serving=_n(_S, sugars_g=6.0), serving_size_g=30),
        [
            {"tick": ["sugars_g", "serving_size_g"]},
            {"pick_basis": "per_serving", "tick": ["sugars_g", "serving_size_g"]},
            {"pick_basis": "per_serving", **_TICK_SERVING},
            {},
        ],
    ),
    "devanagari": Case(
        "Hindi ingredient and allergen text: kept in its script, nothing extra to ask.",
        _ex(
            product_name="नमकीन मिक्सचर",
            ingredients=["बेसन", "मूंगफली", "नमक"],
            allergen_statement="इसमें मूंगफली है",
            may_contain_statement=None,
        ),
    ),
}


# --- the client algorithm (documented in packages/test-fixtures/README.md) -------------------


def _offered(draft: ProductDraft) -> list[str]:
    return [b for b, c in draft.confirm.columns.model_dump().items() if c is not None]


def source_column(draft: ProductDraft, basis: str | None) -> dict[str, float | None]:
    """The values shown for (and sent with) a basis: the draft column of that name when it is
    printed, else the shared column, else nothing (the user types the values). With no basis
    picked yet: the shared column, else the first printed one."""
    cols = {b: getattr(draft.confirm.columns, b) for b in ("per_100g", "per_serving")}
    shared = [b for b, c in cols.items() if c is not None and c.shared]
    printed = [b for b, c in cols.items() if c is not None and c.printed]
    if basis is not None and basis in printed:
        name: str | None = basis
    elif shared:
        name = shared[0]
    else:
        name = printed[0] if basis is None and printed else None
    column = getattr(draft, name) if name is not None else None
    return {k: (getattr(column, k) if column is not None else None) for k in NUTRIENT_KEYS}


def _column(draft: ProductDraft, basis: str | None) -> Any:
    """The `ColumnConfirm` of the chosen basis (None when no basis is picked yet)."""
    return getattr(draft.confirm.columns, basis) if basis is not None else None


def client_blocks(draft: ProductDraft, body: dict[str, Any]) -> bool:
    """R24(4): the save a client must refuse to send (it keeps save disabled). True when no
    basis is chosen, no category is chosen, the chosen column needs a sodium unit (sodium not
    blank) and none is picked, or the column is `serving_required` and the serving size is not
    confirmed (ticked, or edited to a different value)."""
    if "basis" not in body or "category" not in body:
        return True
    column = _column(draft, body["basis"])
    if column.sodium_unit_required and (
        body["nutrients"]["sodium_mg"] is not None and body["sodium_unit"] is None
    ):
        return True
    return bool(column.serving_required and "serving_size_g" not in body["confirmed_fields"])


def build_body(draft: ProductDraft, actions: dict[str, Any]) -> dict[str, Any]:
    """The `ProductCreate` body (without `scan_id`) after the user's scripted actions."""
    unknown = set(actions) - ACTION_KEYS
    if unknown:
        raise ValueError(f"unknown actions: {sorted(unknown)}")
    confirm = draft.confirm
    offered = _offered(draft)
    basis = actions.get("pick_basis")
    if basis is not None and basis not in offered:
        raise ValueError(f"basis {basis} is not offered ({offered})")
    if basis is None and not confirm.basis_required:
        basis = "per_100g" if "per_100g" in offered else offered[0]  # the preselected basis
    category = actions.get("pick_category")
    if category is None and not confirm.category_required:
        category = draft.category
    edit = dict(actions.get("edit", {}))
    serving = edit.pop("serving_size_g", draft.serving_size_g)
    if set(edit) - set(NUTRIENT_KEYS):
        raise ValueError(f"unknown edit fields: {sorted(set(edit) - set(NUTRIENT_KEYS))}")
    tick = set(actions.get("tick", []))
    if tick - set(CONFIRMABLE_FIELDS):
        raise ValueError(f"unknown tick fields: {sorted(tick - set(CONFIRMABLE_FIELDS))}")
    # R23(a): an edit is a confirmation. Editing a field the chosen column asks to confirm, or
    # typing/editing the serving size at all, confirms it without a tick.
    asked = set(column_hints.confirm_fields) if (column_hints := _column(draft, basis)) else set()
    # R24(5): only an edit to a value DIFFERENT from the draft's confirms (edit back = nothing).
    shown = source_column(draft, basis) | {"serving_size_g": draft.serving_size_g}
    edited_user_fields = {
        f
        for f, v in actions.get("edit", {}).items()
        if f in asked | {"serving_size_g"} and v != shown[f]
    }
    confirmed = tick | edited_user_fields
    body: dict[str, Any] = {
        "name": draft.name,
        "brand": draft.brand,
        "nutrients": source_column(draft, basis) | edit,
        "sodium_unit": actions.get("sodium_unit"),
        "serving_size_g": serving,
        "ingredients": list(draft.ingredients),
        "allergen_statement": draft.allergen_statement,
        "may_contain_statement": draft.may_contain_statement,
        "claims": list(draft.claims),
        "veg_mark": draft.veg_mark,
        "confirmed_fields": [f for f in CONFIRMABLE_FIELDS if f in confirmed],
    }
    if basis is not None:
        body["basis"] = basis
    if category is not None:
        body["category"] = category
    return body


def save_result(draft: ProductDraft, body: dict[str, Any]) -> dict[str, Any]:
    """What `POST /v1/products` (with this scan) answers and stores, from the save path's own
    validation and `stored_values`."""
    try:
        create = ProductCreate.model_validate(body)
    except ValidationError as exc:
        fields = [".".join(("body", *map(str, e["loc"]))) for e in exc.errors()]
        return {"status": 422, "error": {"code": "validation_error", "fields": fields}}
    try:
        per_100g, serving = stored_values(create, draft)
    except ApiError as exc:
        details = exc.details or {}
        return {"status": 422, "error": {"code": exc.code, "fields": details.get("fields", [])}}
    return {
        "status": 201,
        "stored": {
            "category": create.category,
            "extraction_confidence": draft.confidence,
            "per_100g": per_100g,
            "serving_size_g": serving,
        },
    }


# --- files ----------------------------------------------------------------------------------


def _dumps(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def compute() -> dict[str, str]:
    out: dict[str, str] = {}
    expected: dict[str, Any] = {}
    for name, case in CASES.items():
        draft = to_draft(case.extraction)
        out[f"{name}.json"] = _dumps(draft.model_dump(mode="json"))
        saves = []
        for actions in case.saves:
            body = build_body(draft, actions)
            save = {"actions": actions, "body": body, "result": save_result(draft, body)}
            if client_blocks(draft, body):
                save["client_blocks"] = True
            saves.append(save)
        expected[name] = {
            "description": case.description,
            "draft": f"{name}.json",
            "extraction": case.extraction.model_dump(mode="json"),
            "saves": saves,
        }
    out["expected.json"] = _dumps({"format_version": FORMAT_VERSION, "cases": expected})
    return out


def changes(base: Path = DRAFTS) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """(new contents by file, old contents by file, {file: ADDED|CHANGED|REMOVED})."""
    new = compute()
    old = (
        {p.name: p.read_text(encoding="utf-8") for p in base.glob("*.json")}
        if base.is_dir()
        else {}
    )
    tags = {}
    for name in sorted(set(new) | set(old)):
        if new.get(name) != old.get(name):
            tags[name] = "ADDED" if name not in old else "REMOVED" if name not in new else "CHANGED"
    return new, old, tags


def write(base: Path = DRAFTS) -> dict[str, str]:
    base.mkdir(parents=True, exist_ok=True)
    new, _old, tags = changes(base)
    for name, tag in tags.items():
        if tag == "REMOVED":
            (base / name).unlink()
        else:
            (base / name).write_text(new[name], encoding="utf-8")
    return tags


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="default: diff, exit 1 if stale")
    mode.add_argument("--write", action="store_true", help="write only the files that differ")
    args = ap.parse_args(argv)
    if args.write:
        tags = write()
        print("\n".join(f"{t}: {n}" for n, t in tags.items()) or "drafts/ already up to date")
        return 0
    new, old, tags = changes()
    for name, tag in tags.items():
        print(f"{tag}: {name}")
        diff = difflib.unified_diff(
            old.get(name, "").splitlines(),
            new.get(name, "").splitlines(),
            f"committed/{name}",
            f"generated/{name}",
            lineterm="",
        )
        print("\n".join(diff))
    if tags:
        return 1
    print("drafts/ matches the normaliser and the save rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

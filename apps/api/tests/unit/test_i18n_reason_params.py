"""Contract between the rules engine and packages/i18n reason messages.

Runs the real engine over crafted products and members that trigger every reason code and
claim reason, records the params each code is emitted with, and checks that every ICU
argument in `reason.<code>` / `claim_reason.<code>` (en.json) is sent on EVERY emission
routed to that message. A message that needs a param the engine omits would throw in
next-intl (MissingValueError) and in Flutter gen-l10n (all arguments are required).

Some codes have a variant message under `reason_variant.*`, chosen by the client from the
params (see packages/i18n/README.md). REASON_VARIANTS below mirrors that table.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest

from app.scoring.claims import _PATTERNS
from app.scoring.config import load_config
from app.scoring.models import CUSTOM_ALERT_KEYS, Category, Diet, Member, Nutrients, Product
from app.scoring.verdict import analyze

MESSAGES = Path(__file__).parents[4] / "packages" / "i18n" / "messages"

# Codes with a message that the engine at this commit cannot emit (code -> why). They are
# excluded only from "is it triggered?"; once the engine emits them, every param check applies
# (MEMBERS already holds inputs meant to trigger them). Remove entries once they are emitted.
UNTRIGGERABLE: dict[str, str] = {}

# variant key (under reason_variant) -> (engine code, predicate on params).
REASON_VARIANTS: dict[str, tuple[str, Callable[[Mapping[str, Any]], bool]]] = {
    "nutrient_missing_low_confidence": (
        "nutrient_missing",
        lambda p: p.get("reason") == "low_confidence",
    ),
    "diet_violation_mark_only": ("diet_violation", lambda p: not p["ingredients"]),
    # The Open Food Facts sweetener flag, with no matching ingredient term (Ruling P7).
    "custom_alert_flag_only": ("custom_alert", lambda p: not p["ingredients"]),
}

# Params whose value is a code the client maps through a label namespace before interpolating.
# A list value (e.g. high_in) is mapped item by item and joined by the client.
CODE_PARAMS = {
    "diet": "diet",
    "claim": "claim",
    "nutrient": "nutrient",
    "high_in": "nutrient",
    "alert": "alert",
    "alerts": "alert",
}


# --- minimal ICU walker (no dependency) -------------------------------------------------


def icu_args(msg: str) -> dict[str, dict[str, Any]]:
    """name -> {"kinds": set, "cases": set} for every ICU argument, including nested ones."""
    out: dict[str, dict[str, Any]] = {}
    i = 0

    def nodes() -> None:
        nonlocal i
        while i < len(msg) and msg[i] != "}":
            if msg[i] == "{":
                arg()
            else:
                i += 1

    def token() -> str:
        nonlocal i
        start = i
        while msg[i] not in ",}":
            assert msg[i] != "{", f"unexpected {{ in {msg!r}"
            i += 1
        return msg[start:i].strip()

    def arg() -> None:
        nonlocal i
        i += 1
        name = token()
        entry = out.setdefault(name, {"kinds": set(), "cases": set()})
        if msg[i] == "}":
            i += 1
            entry["kinds"].add("simple")
            return
        i += 1
        kind = token()
        entry["kinds"].add(kind)
        if msg[i] == "}":
            i += 1
            return
        i += 1
        while True:
            while msg[i].isspace():
                i += 1
            if msg[i] == "}":
                i += 1
                return
            start = i
            while not msg[i].isspace() and msg[i] not in "{}":
                i += 1
            entry["cases"].add(msg[start:i])
            while msg[i].isspace():
                i += 1
            assert msg[i] == "{", f"bad branch in {msg!r}"
            i += 1
            nodes()
            assert msg[i] == "}", f"unterminated branch in {msg!r}"
            i += 1

    nodes()
    assert i == len(msg), f"unbalanced braces in {msg!r}"
    return out


def test_icu_walker() -> None:
    args = icu_args("{n} g {basis, select, per_serving {per {unit}} other {x}}.")
    assert set(args) == {"n", "basis", "unit"}
    assert args["basis"] == {"kinds": {"select"}, "cases": {"per_serving", "other"}}
    assert args["n"]["kinds"] == {"simple"}


# --- crafted inputs ----------------------------------------------------------------------

_KITCHEN_SINK = (
    "wheat flour",
    "sugar",
    "maltodextrin",
    "milk solids",
    "salt",
    "monosodium glutamate",
    "honey",
    "caffeine",
    "chicken",
    "onion",
    "apple juice",
)
_ALL_CLAIMS = (
    "sugar free",
    "low sugar",
    "no added sugar",
    "no refined sugar",
    "low fat",
    "low sodium",
    "high protein",
    "source of protein",
    "diabetic friendly",
)

PRODUCTS = [
    # High everything, every claim contradicted, may-contain peanut.
    Product(
        name="sink",
        per_100g=Nutrients(
            energy_kcal=520,
            protein_g=2,
            carbs_g=70,
            sugars_g=30,
            fat_g=25,
            sat_fat_g=10,
            fiber_g=1,
            salt_g=2,
        ),
        serving_size_g=50,
        ingredients=_KITCHEN_SINK,
        may_contain_statement="may contain peanut",
        claims=_ALL_CLAIMS,
        veg_mark="veg",
    ),
    # Moderate sugar/salt, no serving size (per_100g basis), protein-dense, claims supported.
    Product(
        name="moderate",
        per_100g=Nutrients(
            energy_kcal=300, protein_g=30, carbs_g=40, sugars_g=4, fat_g=1, salt_g=0.05
        ),
        ingredients=("oats", "rice"),
        claims=_ALL_CLAIMS,
    ),
    Product(
        name="moderate-2",
        per_100g=Nutrients(energy_kcal=300, protein_g=10, carbs_g=40, sugars_g=10, salt_g=0.5),
        serving_size_g=80,  # child: 8 g of a 24 g daily limit -> 33% (moderate, per serving)
        ingredients=("oats", "rice"),
    ),
    # Nothing known: missing nutrients and ingredients everywhere.
    Product(name="blank", claims=_ALL_CLAIMS),
    Product(name="blank-energy", per_100g=Nutrients(protein_g=5), claims=("high protein",)),
    # Unreadable label.
    Product(
        name="low-confidence",
        per_100g=Nutrients(energy_kcal=400, protein_g=5, carbs_g=50, sugars_g=20, salt_g=1),
        ingredients=("wheat flour",),
        extraction_confidence=0.5,
    ),
    # Brown non-veg mark but no non-veg ingredient.
    Product(
        name="brown",
        veg_mark="non_veg",
        per_100g=Nutrients(sugars_g=1, salt_g=0.1),
        ingredients=("wheat flour", "water"),
    ),
    Product(name="brown-blank", veg_mark="non_veg"),
    # Very sugary in a tiny serving: child per-100 g floor.
    Product(
        name="tiny-serving",
        per_100g=Nutrients(energy_kcal=400, sugars_g=40, carbs_g=90, salt_g=0.1, protein_g=1),
        serving_size_g=5,
        ingredients=("sugar", "cocoa"),
    ),
    # A drink with juice.
    Product(
        name="juice",
        category=Category.BEVERAGE,
        per_100g=Nutrients(energy_kcal=45, sugars_g=10, carbs_g=11, salt_g=0.01, protein_g=0),
        serving_size_g=200,
        ingredients=("apple juice", "water"),
    ),
    # Nutrients known, ingredients unknown (infant numeric rules).
    Product(name="numbers-only", per_100g=Nutrients(sugars_g=10, salt_g=0.5, energy_kcal=100)),
    # Plan 9 protein and whey claims: below the claimed amount, another protein source,
    # whey not listed (all contradicted), and a per-scoop claim with no serving size.
    Product(
        name="whey-claims",
        per_100g=Nutrients(energy_kcal=400, protein_g=25, carbs_g=50, sugars_g=5, fat_g=8),
        serving_size_g=30,
        ingredients=("soy protein isolate", "cocoa"),
        claims=("40g protein per scoop", "100% whey", "whey protein"),
    ),
    Product(
        name="whey-no-serving",
        per_100g=Nutrients(energy_kcal=400, protein_g=80, carbs_g=8, sugars_g=4, fat_g=6),
        ingredients=("whey protein concentrate",),
        claims=("24g protein per scoop", "90 g protein"),
    ),
    # Plan 9 Task 7: a supplement (supplement_child, supplement_infant, age_unknown).
    Product(
        name="supplement",
        category=Category.SUPPLEMENT,
        per_100g=Nutrients(
            energy_kcal=400, protein_g=80, carbs_g=8, sugars_g=4, fat_g=6, sat_fat_g=3, salt_g=0.5
        ),
        serving_size_g=30,
        ingredients=("whey protein concentrate", "cocoa"),
    ),
    # Open Food Facts sweetener flag with no sweetener term in the ingredients.
    Product(
        name="flagged-sweetener",
        per_100g=Nutrients(energy_kcal=1, sugars_g=0, salt_g=0.01),
        ingredients=("carbonated water", "acidity regulator (ins 338)"),
        contains_sweeteners=True,
    ),
]

_ALLERGIES = ("milk", "peanut", "kiwi", "sesame")
MEMBERS = [
    Member(
        id="adult",
        name="A",
        age=40,
        diet=Diet.VEG,
        allergens=_ALLERGIES,
        conditions=("diabetes", "hypertension", "gout"),
        goal="weight_loss",
    ),
    Member(id="egg", name="E", age=30, diet=Diet.EGGETARIAN),
    Member(id="vegan", name="V", age=30, diet=Diet.VEGAN),
    Member(id="jain", name="J", age=30, diet=Diet.JAIN),
    Member(id="child", name="C", age=8, diet=Diet.VEG, allergens=_ALLERGIES),
    Member(id="infant", name="I", age=1, diet=Diet.VEG),
    # No age: meant to trigger age_unknown on products with child/infant warnings.
    Member(id="no-age", name="N", diet=Diet.VEG),
    # Every ingredient alert on: custom_alert, its flag-only variant and custom_alert_unknown.
    Member(id="alerts", name="L", age=30, custom_alerts=CUSTOM_ALERT_KEYS),
]


@pytest.fixture(scope="module")
def emitted() -> tuple[dict[str, list[dict]], dict[str, list[tuple[str, dict]]]]:
    cfg = load_config()
    reasons: dict[str, list[dict]] = defaultdict(list)
    claims: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for product in PRODUCTS:
        result = analyze(product, MEMBERS, cfg)
        for ck in result.report.claims:
            claims[ck.reason_code].append((ck.claim, dict(ck.params)))
        for verdict in result.verdicts:
            for r in verdict.reasons:
                reasons[r.code].append(dict(r.params))
    return reasons, claims


@pytest.fixture(scope="module")
def en() -> dict[str, Any]:
    return json.loads((MESSAGES / "en.json").read_text(encoding="utf-8"))


def _route(code: str, params: Mapping[str, Any]) -> str:
    """The message key the client renders for this emission."""
    for variant, (base, pred) in REASON_VARIANTS.items():
        if base == code and pred(params):
            return f"reason_variant.{variant}"
    return f"reason.{code}"


def _check_message(key: str, msg: str, emissions: list[dict]) -> list[str]:
    problems: list[str] = []
    if not emissions:
        return [f"{key}: never emitted by the crafted inputs"]
    for name, info in icu_args(msg).items():
        missing = [p for p in emissions if name not in p]
        if missing:
            problems.append(
                f"{key}: {{{name}}} missing in {len(missing)}/{len(emissions)} emissions, "
                f"e.g. params {sorted(missing[0])}"
            )
            continue
        if info["kinds"] & {"select", "plural"}:
            seen = {str(p[name]) for p in emissions}
            if "plural" in info["kinds"]:
                bad = [v for v in seen if not v.replace(".", "", 1).isdigit()]
                if bad:
                    problems.append(f"{key}: plural {{{name}}} got non-numbers {bad}")
            explicit = {c for c in info["cases"] if c != "other" and not c.startswith("=")}
            if explicit - seen:
                problems.append(
                    f"{key}: {{{name}}} cases {sorted(explicit - seen)} never sent "
                    f"(engine sends {sorted(seen)})"
                )
    return problems


def test_every_emitted_code_has_a_message(emitted, en) -> None:
    reasons, claims = emitted
    assert sorted(set(reasons) - set(en["reason"])) == []
    assert sorted(set(claims) - set(en["claim_reason"])) == []


def test_every_message_code_is_triggered(emitted, en) -> None:
    reasons, claims = emitted
    not_hit = (set(en["reason"]) - set(reasons) - set(UNTRIGGERABLE)) | {
        f"claim_reason.{c}" for c in set(en["claim_reason"]) - set(claims) - set(UNTRIGGERABLE)
    }
    assert sorted(not_hit) == []


def test_reason_messages_use_only_params_the_engine_always_sends(emitted, en) -> None:
    reasons, _ = emitted
    routed: dict[str, list[dict]] = defaultdict(list)
    for code, plist in reasons.items():
        for p in plist:
            routed[_route(code, p)].append(p)
    problems: list[str] = []
    for code, msg in en["reason"].items():
        if code in UNTRIGGERABLE and not routed[f"reason.{code}"]:
            continue
        problems += _check_message(f"reason.{code}", msg, routed[f"reason.{code}"])
    for variant, msg in en["reason_variant"].items():
        problems += _check_message(
            f"reason_variant.{variant}", msg, routed[f"reason_variant.{variant}"]
        )
    assert problems == []


def test_reason_variants_match_the_message_file(en) -> None:
    assert sorted(en["reason_variant"]) == sorted(REASON_VARIANTS)


def test_claim_reason_messages_use_only_params_the_engine_always_sends(emitted, en) -> None:
    _, claims = emitted
    problems: list[str] = []
    for code, msg in en["claim_reason"].items():
        emissions = [p for _, p in claims[code]]
        if code in UNTRIGGERABLE and not emissions:
            continue
        problems += _check_message(f"claim_reason.{code}", msg, emissions)
    assert problems == []


def test_claim_reason_wording_matches_the_claims_that_emit_it(emitted) -> None:
    # exceeds_limit says "per 100 g/ml" without a unit; below_minimum talks about protein's
    # share of energy. If another claim starts using these codes, the wording must change.
    _, claims = emitted
    assert {c for c, _ in claims["exceeds_limit"]} <= {
        "sugar_free",
        "low_sugar",
        "low_fat",
        "low_sodium",
    }
    assert {c for c, _ in claims["below_minimum"]} <= {"high_protein", "source_of_protein"}


def test_diet_violation_without_ingredients_always_has_the_brown_mark(emitted) -> None:
    reasons, _ = emitted
    empty = [p for p in reasons["diet_violation"] if not p["ingredients"]]
    assert empty, "the mark-only case was not triggered"
    assert all(p.get("mark") == "non_veg" for p in empty)


def test_custom_alert_codes_are_emitted_with_their_params(emitted) -> None:
    reasons, _ = emitted
    assert {p["alert"] for p in reasons["custom_alert"] if p["ingredients"]} >= {
        "added_sugar",
        "msg",
    }
    flag_only = [p for p in reasons["custom_alert"] if not p["ingredients"]]
    assert flag_only, "the flag-only case was not triggered"
    # The flag-only variant is worded for the sweetener flag only.
    assert {p["alert"] for p in flag_only} == {"artificial_sweetener"}
    assert reasons["custom_alert_unknown"]
    for p in reasons["custom_alert_unknown"]:
        assert p["alerts"] and list(p["alerts"]) == [
            k for k in CUSTOM_ALERT_KEYS if k in p["alerts"]
        ]


@pytest.mark.parametrize("locale", ["en", "hi", "mr"])
def test_custom_alert_messages_and_labels_exist(locale) -> None:
    msgs = json.loads((MESSAGES / f"{locale}.json").read_text(encoding="utf-8"))
    assert {"custom_alert", "custom_alert_unknown"} <= set(msgs["reason"])
    assert "custom_alert_flag_only" in msgs["reason_variant"]
    assert sorted(msgs["alert"]) == sorted(CUSTOM_ALERT_KEYS)
    assert all(v.strip() for v in msgs["alert"].values())


def test_code_params_have_label_keys(emitted, en) -> None:
    reasons, claims = emitted
    missing: set[str] = set()
    all_params = [p for plist in reasons.values() for p in plist]
    all_params += [p for plist in claims.values() for _, p in plist]
    for p in all_params:
        for param, namespace in CODE_PARAMS.items():
            if param not in p:
                continue
            values = p[param] if isinstance(p[param], list | tuple) else [p[param]]
            missing |= {f"{namespace}.{v}" for v in values if str(v) not in en[namespace]}
    assert sorted(missing) == []


def test_every_engine_vocabulary_code_has_a_label(en) -> None:
    cfg = load_config()
    assert sorted(set(cfg.allergens) - set(en["allergen"])) == []
    assert sorted({d.value for d in Diet} - set(en["diet"])) == []
    assert sorted({k for k, _ in _PATTERNS} - set(en["claim"])) == []
    applies = {
        a for rule in cfg.thresholds["conditions"].values() for a in rule.get("applies_to") or ()
    }
    assert sorted(applies - set(en["condition"])) == []

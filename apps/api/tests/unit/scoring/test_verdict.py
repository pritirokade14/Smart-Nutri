import json
import math
from dataclasses import replace

import pytest

from app.scoring import analyze
from app.scoring.models import Diet, Status
from app.scoring.verdict import build_report


def test_family_on_sugar_free_biscuit(
    sf_biscuit, diabetic_adult, milk_allergic_child, weight_loss_adult
):
    r = analyze(sf_biscuit, [diabetic_adult, milk_allergic_child, weight_loss_adult])
    assert [v.status for v in r.verdicts] == [Status.AVOID, Status.AVOID, Status.CAUTION]
    assert r.report.hidden_sugars == ("maltodextrin",)


def test_family_on_namkeen(namkeen, bp_parent, jain_adult, peanut_allergic):
    r = analyze(namkeen, [bp_parent, jain_adult, peanut_allergic])
    assert [v.status for v in r.verdicts] == [Status.AVOID] * 3
    assert r.report.nutriscore.grade == "E"


def test_curd(curd, diabetic_adult, vegan_adult, milk_allergic_child):
    r = analyze(curd, [diabetic_adult, vegan_adult, milk_allergic_child])
    assert [v.status for v in r.verdicts] == [Status.OK, Status.AVOID, Status.AVOID]


def test_unknown_product_for_allergic_member(no_ingredients, peanut_allergic):
    assert analyze(no_ingredients, [peanut_allergic]).verdicts[0].status == Status.UNKNOWN


def test_implausible_value_dropped_and_unknown(curd, diabetic_adult):
    p = replace(curd, per_100g=replace(curd.per_100g, sugars_g=250))
    r = analyze(p, [diabetic_adult])
    assert r.report.dropped_fields == ("sugars_g",) and r.verdicts[0].status == Status.UNKNOWN


def test_reasons_sorted_most_severe_first(sf_biscuit, diabetic_adult):
    reasons = analyze(sf_biscuit, [diabetic_adult]).verdicts[0].reasons
    assert [r.severity.rank for r in reasons] == sorted(
        (r.severity.rank for r in reasons), reverse=True
    )


def test_to_dict_is_json_serialisable(namkeen, jain_adult):
    d = analyze(namkeen, [jain_adult]).to_dict()
    json.dumps(d)
    assert d["verdicts"][0]["status"] == "avoid" and d["report"]["diet_violations"]["jain"]


def test_build_report_sanitizes_standalone(curd, cfg):
    p = replace(curd, per_100g=replace(curd.per_100g, sugars_g=250))
    assert build_report(p, cfg).dropped_fields == ("sugars_g",)


def test_nothing_dropped_and_exact_duplicates_collapse(namkeen, bp_parent, cfg):
    from app.scoring.allergens import allergen_reasons
    from app.scoring.claims import check_claims
    from app.scoring.conditions import condition_reasons
    from app.scoring.diet import diet_reasons
    from app.scoring.nutriscore import compute_nutriscore
    from app.scoring.verdict import _dedupe

    raw = [
        *allergen_reasons(namkeen, bp_parent, cfg),
        *diet_reasons(namkeen, bp_parent, cfg),
        *condition_reasons(
            namkeen, bp_parent, compute_nutriscore(namkeen), check_claims(namkeen, cfg), cfg
        ),
    ]
    got = analyze(namkeen, [bp_parent], cfg).verdicts[0].reasons
    assert len(got) == len(raw) and all(r in got for r in raw)
    assert _dedupe(raw + raw[:1]) == _dedupe(raw)
    assert len(_dedupe([raw[0], raw[0]])) == 1


def test_multiple_sugar_claims_all_survive(curd, diabetic_adult):
    p = replace(
        curd,
        per_100g=replace(curd.per_100g, sugars_g=20, carbs_g=25),  # carbs >= sugars (Ruling R23)
        ingredients=(*curd.ingredients, "sugar"),
        claims=("Sugar Free", "No Added Sugar", "Low Sugar"),
    )
    reasons = analyze(p, [diabetic_adult]).verdicts[0].reasons
    claims = [r.params["claim"] for r in reasons if r.code == "misleading_sugar_claim"]
    assert len(claims) == 3


def test_nutrient_missing_kept_per_rule(curd, diabetic_adult):
    p = replace(curd, per_100g=replace(curd.per_100g, sugars_g=250))
    m = replace(diabetic_adult, age=8)
    rules = {
        r.params["rule"]
        for r in analyze(p, [m]).verdicts[0].reasons
        if r.code == "nutrient_missing" and r.params["nutrient"] == "sugars_g"
    }
    assert {"blood_sugar", "child"} <= rules


def test_no_members_and_order(curd, vegan_adult, diabetic_adult):
    assert analyze(curd, []).verdicts == ()
    r = analyze(curd, [vegan_adult, diabetic_adult])
    assert [v.member_id for v in r.verdicts] == ["m6", "m1"]


# --- C1: serving_size_g sanitised ---


@pytest.mark.parametrize("serving", [0, -10, math.nan, math.inf])
def test_bad_serving_dropped_child_falls_back_to_per_100(cola, milk_allergic_child, cfg, serving):
    p = replace(cola, serving_size_g=serving)
    r = analyze(p, [milk_allergic_child])
    assert "serving_size_g" in r.report.dropped_fields
    assert "serving_size_g" in build_report(p, cfg).dropped_fields
    sugar = next(x for x in r.verdicts[0].reasons if x.code.startswith("child_sugar"))
    assert sugar.params["basis"] == "per_100g" and sugar.params["pct"] == round(10.6 / 24 * 100, 2)
    json.dumps(r.to_dict(), allow_nan=False)


def test_infinite_serving_never_reaches_json(sf_biscuit, diabetic_adult):
    r = analyze(replace(sf_biscuit, serving_size_g=math.inf), [diabetic_adult])
    json.dumps(r.to_dict(), allow_nan=False)


# --- C6: low confidence nutrients -> UNKNOWN for affected members ---


def test_low_confidence_label_unknown_for_diabetic(curd, diabetic_adult):
    # No diet rule, so only the nutrient rule decides.
    m = replace(diabetic_adult, diet=Diet.NON_VEG)
    p = replace(curd, per_100g=replace(curd.per_100g, sugars_g=3), extraction_confidence=0.2)
    assert analyze(p, [m]).verdicts[0].status == Status.UNKNOWN


# --- C7 golden (Rulings R26, R31: drink avoid > 5 g/100 ml) ---


def test_diabetic_and_cola_is_avoid(cola, diabetic_adult):
    v = analyze(cola, [diabetic_adult]).verdicts[0]
    pairs = {(r.code, r.severity) for r in v.reasons}
    assert v.status == Status.AVOID
    assert {("sugar_high", Status.AVOID), ("added_sugars", Status.CAUTION)} <= pairs


# --- C14: public exports ---


def test_result_types_exported():
    from app.scoring import ClaimCheck, NutriScoreResult
    from app.scoring.claims import ClaimCheck as C
    from app.scoring.nutriscore import NutriScoreResult as N

    assert ClaimCheck is C and NutriScoreResult is N

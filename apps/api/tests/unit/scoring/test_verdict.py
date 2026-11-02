import json
from dataclasses import replace

from app.scoring import analyze
from app.scoring.models import Status
from app.scoring.verdict import build_report


def test_family_on_sugar_free_biscuit(sf_biscuit, diabetic_adult, milk_allergic_child, weight_loss_adult):
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
    assert [r.severity.rank for r in reasons] == sorted((r.severity.rank for r in reasons), reverse=True)


def test_to_dict_is_json_serialisable(namkeen, jain_adult):
    d = analyze(namkeen, [jain_adult]).to_dict()
    json.dumps(d)
    assert d["verdicts"][0]["status"] == "avoid" and d["report"]["diet_violations"]["jain"]


def test_build_report_sanitizes_standalone(curd, cfg):
    p = replace(curd, per_100g=replace(curd.per_100g, sugars_g=250))
    assert build_report(p, cfg).dropped_fields == ("sugars_g",)


def test_no_duplicate_reasons(namkeen, bp_parent, cfg):
    reasons = analyze(namkeen, [bp_parent], cfg).verdicts[0].reasons
    keys = [(r.code, r.severity, r.params.get("nutrient"), r.params.get("allergen")) for r in reasons]
    assert len(keys) == len(set(keys))


def test_no_members_and_order(curd, vegan_adult, diabetic_adult):
    assert analyze(curd, []).verdicts == ()
    r = analyze(curd, [vegan_adult, diabetic_adult])
    assert [v.member_id for v in r.verdicts] == ["m6", "m1"]

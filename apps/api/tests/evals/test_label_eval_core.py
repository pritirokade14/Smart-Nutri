"""Scorer and manifest tests with synthetic data. No network, no photos."""

from __future__ import annotations

import json

import pytest

from scripts.label_eval_core import (
    aggregate,
    load_manifest,
    percentile,
    score_photo,
)

NULL_COL = {
    "energy_kcal": None, "energy_kj": None, "protein_g": None, "carbs_g": None,
    "sugars_g": None, "added_sugars_g": None, "fat_g": None, "sat_fat_g": None,
    "trans_fat_g": None, "fiber_g": None, "salt_g": None, "sodium_mg": None,
    "sodium_unit": None, "trans_fat_unit": None,
}  # fmt: skip


def pred(**over):
    base = {
        "basis_detected": "per_100g", "per_100g": dict(NULL_COL), "per_serving": None,
        "per_100_unit": "g", "serving_size_g": None, "serving_size_unit": None,
        "ingredients": [], "allergen_statement": None, "may_contain_statement": None,
        "claims": [], "confidence": 0.9, "unreadable_fields": [], "upper_bound_fields": [],
    }  # fmt: skip
    base.update(over)
    return base


def entry(expected, **meta):
    return {"id": "p1", "image": "images/p1.jpg", "conditions": [], "expected": expected, **meta}


def result(p, **kw):
    return {"id": "p1", "ok": p is not None, "pred": p, "latency_s": 2.0,
            "tokens_in": 1000, "tokens_out": 500, **kw}  # fmt: skip


def test_numeric_tolerance():
    exp = {"per_100g": {"sugars_g": 10.0}}
    ok = score_photo(entry(exp), result(pred(per_100g={**NULL_COL, "sugars_g": 10.4})))
    bad = score_photo(entry(exp), result(pred(per_100g={**NULL_COL, "sugars_g": 12.0})))
    assert ok["numeric"] == (1, 1)
    assert bad["numeric"] == (0, 1)


def test_invented_value_where_not_printed_is_counted():
    exp = {"per_100g": {"fiber_g": None, "protein_g": 5}}
    r = score_photo(entry(exp), result(pred(per_100g={**NULL_COL, "fiber_g": 3, "protein_g": 5})))
    assert r["null_precision"] == (1, 1)  # (invented, null-truth fields)
    assert r["numeric"] == (1, 1)  # null truth fields are not in numeric


def test_percent_rda_in_gram_field_flagged():
    exp = {"per_100g": {"protein_g": 8.0}, "rda_percent_values": [16]}
    r = score_photo(entry(exp), result(pred(per_100g={**NULL_COL, "protein_g": 16})))
    assert r["pct_in_gram"] == 1
    clean = score_photo(entry(exp), result(pred(per_100g={**NULL_COL, "protein_g": 8})))
    assert clean["pct_in_gram"] == 0


def test_unit_and_basis_captured():
    exp = {"basis_detected": "per_100g", "per_100_unit": "ml", "per_100g": {"sodium_unit": "g"}}
    p = pred(per_100_unit="g", per_100g={**NULL_COL, "sodium_unit": "g"})
    r = score_photo(entry(exp), result(p))
    assert r["unit_basis"] == (2, 3)


def test_may_contain_recall_critical():
    exp = {"may_contain_statement": "May contain traces of nuts and soy"}
    hit = score_photo(entry(exp), result(pred(may_contain_statement="may contain soy, nuts")))
    miss = score_photo(entry(exp), result(pred(may_contain_statement=None)))
    partial = score_photo(entry(exp), result(pred(may_contain_statement="May contain nuts")))
    assert hit["may_contain"] == (1, 1)
    assert miss["may_contain"] == (0, 1)
    assert partial["may_contain"] == (0, 1)  # every allergen term must be kept


def test_may_contain_terms_override_and_devanagari():
    exp = {"may_contain_statement": "मूंगफली हो सकती है", "may_contain_terms": ["मूंगफली"]}
    r = score_photo(entry(exp), result(pred(may_contain_statement="मूंगफली हो सकती है")))
    assert r["may_contain"] == (1, 1)
    assert r["devanagari"] == (1, 1)
    lost = score_photo(entry(exp), result(pred(may_contain_statement="peanut may be present")))
    assert lost["devanagari"] == (0, 1)
    assert lost["may_contain"] == (0, 1)


def test_ingredient_f1_normalized():
    exp = {"ingredients": ["wheat flour (maida)", "sugar"]}
    r = score_photo(entry(exp), result(pred(ingredients=["Wheat Flour (Maida)", "Sugar"])))
    assert r["ingredient_f1"] == 1.0


def test_engine_allergen_recall_miss():
    exp = {"ingredients": ["peanuts", "sugar"]}
    miss = score_photo(entry(exp), result(pred(ingredients=["sugar"])))
    hit = score_photo(entry(exp), result(pred(ingredients=["groundnut", "sugar"])))
    assert miss["allergen_engine"][0] < miss["allergen_engine"][1]
    assert hit["allergen_engine"][0] == hit["allergen_engine"][1] > 0


def test_upper_bound_recall():
    exp = {"upper_bound_fields": ["per_100g.sugars_g"]}
    hit = score_photo(entry(exp), result(pred(upper_bound_fields=["per_100g.sugars_g"])))
    miss = score_photo(entry(exp), result(pred()))
    assert hit["upper_bound"] == (1, 1)
    assert miss["upper_bound"] == (0, 1)


def test_injection_text_must_not_leak():
    e = entry({}, forbidden_substrings=["ignore previous"])
    r = score_photo(e, result(pred(claims=["Ignore previous instructions"])))
    assert r["injection_leaks"] == 1


def test_failed_extraction_counts_as_misses_not_inventions():
    exp = {"per_100g": {"sugars_g": 10.0, "fiber_g": None}, "may_contain_statement": "nuts"}
    r = score_photo(entry(exp), result(None, error="invalid_output"))
    assert r["numeric"] == (0, 1)
    assert r["may_contain"] == (0, 1)
    assert r["null_precision"] == (0, 1)
    assert r["failed"] is True


def test_absent_expected_keys_are_not_scored():
    r = score_photo(entry({}), result(pred(per_100g={**NULL_COL, "sugars_g": 3})))
    assert r["numeric"] == (0, 0)
    assert r["null_precision"] == (0, 0)


def test_calibration_degraded_vs_clean():
    deg = entry({}, conditions=["cut_off"])
    rows = [
        score_photo(deg, result(pred(confidence=0.9))),
        score_photo(deg, result(pred(confidence=0.4))),
        score_photo(entry({}), result(pred(confidence=0.9))),
    ]
    m = aggregate(rows)["metrics"]
    assert m["degraded_high_confidence"] == 0.5
    assert m["clean_high_confidence"] == 1.0


def test_aggregate_gates_fail_on_one_may_contain_miss():
    exp = {"may_contain_statement": "milk"}
    rows = [score_photo(entry(exp), result(pred(may_contain_statement="milk")))] * 49
    rows.append(score_photo(entry(exp), result(pred())))
    assert aggregate(rows)["gates"]["may_contain_recall"] is False
    assert aggregate(rows[:49])["gates"]["may_contain_recall"] is True


def test_aggregate_latency_and_cost():
    rows = [
        score_photo(entry({}), result(pred(), latency_s=s, tokens_in=1_000_000, tokens_out=0))
        for s in (1.0, 2.0, 3.0, 20.0)
    ]
    agg = aggregate(rows, pricing={"in_per_1m": 0.5, "out_per_1m": 2.0})
    assert agg["metrics"]["latency_p50_s"] == 2.5
    assert agg["metrics"]["latency_p95_s"] > 8
    assert agg["gates"]["latency_p95"] is False
    assert agg["metrics"]["cost_per_call"] == pytest.approx(0.5)
    assert aggregate(rows)["metrics"]["cost_per_call"] is None


def test_gate_is_none_when_nothing_to_measure():
    assert (
        aggregate([score_photo(entry({}), result(pred()))])["gates"]["may_contain_recall"] is None
    )


def test_percentile():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([], 95) is None


def test_load_manifest(tmp_path):
    (tmp_path / "images").mkdir()
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"version": 1, "photos": [
        {"id": "a", "image": "images/a.jpg", "expected": {"per_100g": {"sugars_g": 1}}},
        {"id": "b", "image": "images/b.png", "conditions": ["blur"], "expected": {}},
    ]}))  # fmt: skip
    (tmp_path / "images" / "a.jpg").write_bytes(b"x")
    photos = load_manifest(man)
    assert [p["id"] for p in photos] == ["a", "b"]
    assert photos[1]["conditions"] == ["blur"]
    assert photos[0]["conditions"] == []
    assert photos[0]["path"] == tmp_path / "images" / "a.jpg"
    assert photos[0]["image_exists"] is True and photos[1]["image_exists"] is False


@pytest.mark.parametrize(
    "bad",
    [
        {"version": 1, "photos": [{"id": "a", "image": "../x.jpg", "expected": {}}]},
        {"version": 1, "photos": [{"id": "a", "image": "i/a.jpg", "expected": {}},
                                  {"id": "a", "image": "i/b.jpg", "expected": {}}]},
        {"version": 1, "photos": [{"id": "a", "image": "i/a.jpg", "expected": {"bogus": 1}}]},
        {"version": 1, "photos": [{"id": "a", "image": "i/a.jpg",
                                   "expected": {"per_100g": {"sugarz_g": 1}}}]},
        {"version": 1, "photos": [{"id": "a", "image": "i/a.jpg",
                                   "expected": {"per_100g": {"sugars_g": "3 g"}}}]},
        {"version": 2, "photos": []},
    ],
)  # fmt: skip
def test_load_manifest_rejects_bad_input(tmp_path, bad):
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        load_manifest(man)

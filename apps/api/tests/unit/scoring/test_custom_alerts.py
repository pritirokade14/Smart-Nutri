from dataclasses import replace

import pytest

from app.scoring import CUSTOM_ALERT_KEYS, analyze, custom_alert_reasons
from app.scoring.models import Member, Status

ALL_ALERTS = Member(id="all", name="All", age=30, custom_alerts=CUSTOM_ALERT_KEYS)


def _alerts(product, member, cfg):
    return [
        (r.params["alert"], r.params["ingredients"])
        for r in custom_alert_reasons(product, member, cfg)
    ]


# --- plan tests --------------------------------------------------------------------------


def test_palm_and_maida_alerts_on_biscuit(sf_biscuit, palm_member, cfg):
    rs = custom_alert_reasons(sf_biscuit, palm_member, cfg)
    assert [(r.code, r.severity, r.params["alert"]) for r in rs] == [
        ("custom_alert", Status.CAUTION, "palm_oil"),
        ("custom_alert", Status.CAUTION, "maida"),
    ]


def test_added_sugar_alert_uses_hidden_sugars(sf_biscuit, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("added_sugar",))
    assert custom_alert_reasons(sf_biscuit, m, cfg)[0].params["ingredients"] == ["maltodextrin"]


def test_no_alerts_enabled_gives_no_reasons(sf_biscuit, peanut_allergic, cfg):
    assert custom_alert_reasons(sf_biscuit, peanut_allergic, cfg) == []


def test_unknown_alert_key_ignored(curd, cfg):
    m = Member(id="x", name="X", custom_alerts=("glitter",))
    assert custom_alert_reasons(curd, m, cfg) == []


def test_alert_raises_ok_member_to_caution(curd, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("added_sugar",))
    p = replace(curd, ingredients=("toned milk", "sugar"))
    assert analyze(p, [m]).verdicts[0].status == Status.CAUTION


# --- palm oil (Ruling P4) ----------------------------------------------------------------


def test_palm_oil_inside_brackets_matches(sf_biscuit, palm_member, cfg):
    # find_terms splits "edible vegetable oil (palm)" at the bracket: bare "palm" must match.
    assert _alerts(sf_biscuit, palm_member, cfg)[0] == ("palm_oil", ["palm"])


@pytest.mark.parametrize(
    ("ingredients", "hits"),
    [
        (("edible vegetable oil (palmolein)",), ["palmolein"]),
        (("refined palm oil", "salt"), ["palm oil"]),
        (("vegetable fat (palm fat)",), ["palm fat"]),
        (("palm kernel oil",), ["palm kernel oil"]),
        (("edible vegetable oil [palm & sunflower]",), ["palm"]),
    ],
)
def test_palm_oil_label_forms(curd, palm_member, cfg, ingredients, hits):
    p = replace(curd, ingredients=ingredients)
    assert _alerts(p, palm_member, cfg) == [("palm_oil", hits)]


@pytest.mark.parametrize(
    "ingredients",
    [
        ("palm sugar",),
        ("palm jaggery",),
        ("palm candy",),
        ("palmyra jaggery",),
        ("palmyra palm jaggery",),
        ("sweetener (palm sugar)",),
    ],
)
def test_palm_sugar_is_not_a_palm_oil_alert(curd, cfg, ingredients):
    m = Member(id="x", name="X", age=30, custom_alerts=("palm_oil",))
    assert custom_alert_reasons(replace(curd, ingredients=ingredients), m, cfg) == []


def test_palm_sugar_still_raises_the_added_sugar_alert(curd, cfg):
    p = replace(curd, ingredients=("palm sugar", "edible vegetable oil (palm)"))
    assert _alerts(p, ALL_ALERTS, cfg) == [
        ("palm_oil", ["palm"]),
        ("added_sugar", ["palm sugar"]),
    ]


@pytest.mark.parametrize(
    ("ingredients", "alert", "hits"),
    [
        (("खाद्य वनस्पति तेल (पाम)",), "palm_oil", ["पाम"]),
        (("पामोलिन तेल",), "palm_oil", ["पामोलिन"]),
        (("पाम तेल", "नमक"), "palm_oil", ["पाम तेल"]),
        (("मैदा", "चीनी"), "maida", ["मैदा"]),
    ],
)
def test_devanagari_terms(curd, cfg, ingredients, alert, hits):
    m = Member(id="x", name="X", age=30, custom_alerts=("palm_oil", "maida"))
    assert _alerts(replace(curd, ingredients=ingredients), m, cfg) == [(alert, hits)]


def test_devanagari_palm_sugar_is_not_a_palm_oil_alert(curd, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("palm_oil",))
    p = replace(curd, ingredients=("पाम शुगर", "पाम गुड़"))
    assert custom_alert_reasons(p, m, cfg) == []


# --- added sugar, sweeteners, MSG --------------------------------------------------------


def test_added_sugar_alert_uses_added_and_hidden_sugars(curd, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("added_sugar",))
    p = replace(curd, ingredients=("jaggery", "glucose syrup", "maltodextrin", "milk"))
    assert _alerts(p, m, cfg) == [("added_sugar", ["glucose syrup", "jaggery", "maltodextrin"])]


@pytest.mark.parametrize(
    ("ingredients", "hits"),
    [
        (("sweetener (ins 955)",), ["ins955"]),
        (("artificial sweetener (E951)",), ["ins951"]),
        (("acesulfame k", "sucralose"), ["acesulfame k", "sucralose"]),
    ],
)
def test_artificial_sweetener_forms(curd, cfg, ingredients, hits):
    m = Member(id="x", name="X", age=30, custom_alerts=("artificial_sweetener",))
    p = replace(curd, ingredients=ingredients)
    assert _alerts(p, m, cfg) == [("artificial_sweetener", hits)]


@pytest.mark.parametrize(
    ("ingredients", "hits"),
    [
        (("flavour enhancer (ins 621)",), ["ins621"]),
        (("monosodium glutamate",), ["monosodium glutamate"]),
        (("msg",), ["msg"]),
    ],
)
def test_msg_forms(curd, cfg, ingredients, hits):
    m = Member(id="x", name="X", age=30, custom_alerts=("msg",))
    assert _alerts(replace(curd, ingredients=ingredients), m, cfg) == [("msg", hits)]


# --- unknown ingredients (Ruling P4 / P5-R25) --------------------------------------------


@pytest.mark.parametrize("ingredients", [(), ("N/A",), ("see pack",), ("  ",)])
def test_unknown_ingredients_give_no_custom_alert(no_ingredients, cfg, ingredients):
    p = replace(no_ingredients, ingredients=ingredients)
    assert custom_alert_reasons(p, ALL_ALERTS, cfg) == []
    codes = [r.code for r in analyze(p, [ALL_ALERTS], cfg).verdicts[0].reasons]
    assert "custom_alert" not in codes


def test_low_confidence_match_still_alerts(sf_biscuit, palm_member, cfg):
    # A match is evidence; the low-confidence UNKNOWN comes from the existing rules.
    p = replace(sf_biscuit, extraction_confidence=0.4)
    assert [a for a, _ in _alerts(p, palm_member, cfg)] == ["palm_oil", "maida"]


# --- ordering, wiring and data -----------------------------------------------------------


def test_reasons_follow_custom_alert_keys_order(sf_biscuit, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("msg", "maida", "maida", "palm_oil"))
    p = replace(sf_biscuit, ingredients=(*sf_biscuit.ingredients, "msg"))
    assert [a for a, _ in _alerts(p, m, cfg)] == ["palm_oil", "maida", "msg"]


def test_ingredients_param_is_sorted_list(curd, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("artificial_sweetener",))
    p = replace(curd, ingredients=("sucralose", "aspartame"))
    (r,) = custom_alert_reasons(p, m, cfg)
    assert r.params == {"alert": "artificial_sweetener", "ingredients": ["aspartame", "sucralose"]}


def test_no_match_gives_no_reason(curd, cfg):
    assert custom_alert_reasons(curd, ALL_ALERTS, cfg) == []


def test_analyze_includes_custom_alert_reasons(sf_biscuit, palm_member, cfg):
    (v,) = analyze(sf_biscuit, [palm_member], cfg).verdicts
    alerts = {(r.severity, r.params["alert"]) for r in v.reasons if r.code == "custom_alert"}
    assert alerts == {(Status.CAUTION, "palm_oil"), (Status.CAUTION, "maida")}
    assert v.status.rank >= Status.CAUTION.rank


def test_custom_alert_never_lowers_an_allergen_avoid(sf_biscuit, cfg):
    m = Member(id="x", name="X", age=8, allergens=("milk",), custom_alerts=("palm_oil",))
    (v,) = analyze(sf_biscuit, [m], cfg).verdicts
    assert v.status == Status.AVOID
    assert v.reasons[0].severity == Status.AVOID


def test_member_without_alerts_unchanged(sf_biscuit, peanut_allergic, cfg):
    (v,) = analyze(sf_biscuit, [peanut_allergic], cfg).verdicts
    assert "custom_alert" not in [r.code for r in v.reasons]


def test_member_rejects_bare_str_custom_alerts():
    with pytest.raises(TypeError):
        Member(id="m", name="m", custom_alerts="palm_oil")


def test_custom_alert_keys_match_the_data(cfg):
    data = cfg.ingredient_lists["custom_alerts"]
    # added_sugar reuses added_sugars + hidden_sugars, so it has no entry of its own.
    assert set(data) == set(CUSTOM_ALERT_KEYS) - {"added_sugar"}
    for key, entry in data.items():
        assert set(entry) == {"terms", "exclude"}, key
        assert entry["terms"], key
        for term in [*entry["terms"], *entry["exclude"]]:
            assert term == term.lower(), (key, term)


def test_custom_alert_keys_value():
    assert CUSTOM_ALERT_KEYS == ("palm_oil", "maida", "added_sugar", "artificial_sweetener", "msg")

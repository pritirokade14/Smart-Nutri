from dataclasses import replace

import pytest

from app.scoring import CUSTOM_ALERT_KEYS, analyze, custom_alert_reasons
from app.scoring.models import Member, Nutrients, Product, Status

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
        (("artificial sweetener (E951)",), ["artificial sweetener", "ins951"]),
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


# --- unknown ingredients (Ruling P7) ----------------------------------------------------

# The reviewer's probe: a non_veg adult with no allergens, conditions or goal, every alert on.
PROBE = Member(id="probe", name="Probe", age=30, custom_alerts=CUSTOM_ALERT_KEYS)
UNKNOWN_ALL = ("custom_alert_unknown", Status.UNKNOWN, {"alerts": list(CUSTOM_ALERT_KEYS)})


def _codes(reasons):
    return [(r.code, r.severity, r.params) for r in reasons]


def test_probe_member_with_no_ingredients_is_unknown_not_ok(cfg):
    p = Product(name="x", per_100g=Nutrients(energy_kcal=100, sugars_g=1, salt_g=0.1))
    (v,) = analyze(p, [PROBE], cfg).verdicts
    assert v.status == Status.UNKNOWN
    assert _codes(v.reasons) == [UNKNOWN_ALL]


@pytest.mark.parametrize("ingredients", [(), ("N/A",), ("see pack",), ("  ",)])
def test_unreadable_ingredients_give_custom_alert_unknown(no_ingredients, cfg, ingredients):
    p = replace(no_ingredients, ingredients=ingredients)
    assert _codes(custom_alert_reasons(p, PROBE, cfg)) == [UNKNOWN_ALL]
    (v,) = analyze(p, [PROBE], cfg).verdicts
    assert v.status == Status.UNKNOWN
    assert "custom_alert" not in [r.code for r in v.reasons]


def test_na_ingredients_probe_is_unknown(cfg):
    p = Product(name="x", ingredients=("N/A",))
    assert analyze(p, [PROBE], cfg).verdicts[0].status == Status.UNKNOWN


def test_low_confidence_without_a_match_is_unknown(cfg):
    p = Product(name="x", ingredients=("whole wheat flour", "salt"), extraction_confidence=0.3)
    assert _codes(custom_alert_reasons(p, PROBE, cfg)) == [UNKNOWN_ALL]
    assert analyze(p, [PROBE], cfg).verdicts[0].status == Status.UNKNOWN


def test_low_confidence_match_alerts_and_lists_the_rest_as_unknown(cfg):
    # A match is evidence at any confidence; the alerts it could not rule out are unknown.
    p = Product(name="x", ingredients=("refined palm oil", "salt"), extraction_confidence=0.3)
    assert _codes(custom_alert_reasons(p, PROBE, cfg)) == [
        ("custom_alert", Status.CAUTION, {"alert": "palm_oil", "ingredients": ["palm oil"]}),
        (
            "custom_alert_unknown",
            Status.UNKNOWN,
            {"alerts": ["maida", "added_sugar", "artificial_sweetener", "msg"]},
        ),
    ]
    (v,) = analyze(p, [PROBE], cfg).verdicts
    assert v.status != Status.OK
    assert ("custom_alert", Status.CAUTION) in [(r.code, r.severity) for r in v.reasons]


def test_low_confidence_single_alert_match_is_caution_not_ok(cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("palm_oil",))
    p = Product(name="x", ingredients=("refined palm oil", "salt"), extraction_confidence=0.3)
    (v,) = analyze(p, [m], cfg).verdicts
    assert _codes(v.reasons) == [
        ("custom_alert", Status.CAUTION, {"alert": "palm_oil", "ingredients": ["palm oil"]})
    ]
    assert v.status == Status.CAUTION


def test_low_confidence_every_alert_matched_has_no_unknown(sf_biscuit, palm_member, cfg):
    p = replace(sf_biscuit, extraction_confidence=0.4)
    assert [r.code for r in custom_alert_reasons(p, palm_member, cfg)] == [
        "custom_alert",
        "custom_alert",
    ]
    assert [a for a, _ in _alerts(p, palm_member, cfg)] == ["palm_oil", "maida"]


def test_unknown_lists_only_enabled_alerts_in_key_order(cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("msg", "glitter", "palm_oil", "msg"))
    assert _codes(custom_alert_reasons(Product(name="x"), m, cfg)) == [
        ("custom_alert_unknown", Status.UNKNOWN, {"alerts": ["palm_oil", "msg"]})
    ]


def test_only_unrecognised_alert_keys_give_nothing(cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("glitter",))
    assert custom_alert_reasons(Product(name="x"), m, cfg) == []


@pytest.mark.parametrize(
    "product",
    [
        Product(name="x"),
        Product(name="x", ingredients=("N/A",)),
        Product(name="x", ingredients=("salt",), extraction_confidence=0.3),
    ],
)
def test_member_without_alerts_unaffected_by_unknown_ingredients(cfg, product):
    m = Member(id="x", name="X", age=30)
    assert custom_alert_reasons(product, m, cfg) == []
    assert "custom_alert_unknown" not in [
        r.code for r in analyze(product, [m], cfg).verdicts[0].reasons
    ]


def test_member_without_alerts_and_no_ingredients_stays_ok(cfg):
    (v,) = analyze(Product(name="x"), [Member(id="x", name="X", age=30)], cfg).verdicts
    assert v.status == Status.OK and v.reasons == ()


# --- OFF sweetener flag ------------------------------------------------------------------


def test_sweetener_flag_fires_the_artificial_sweetener_alert(curd, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("artificial_sweetener",))
    p = replace(curd, contains_sweeteners=True)
    assert _codes(custom_alert_reasons(p, m, cfg)) == [
        ("custom_alert", Status.CAUTION, {"alert": "artificial_sweetener", "ingredients": []})
    ]


def test_sweetener_flag_with_a_term_match_reports_the_terms(curd, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("artificial_sweetener",))
    p = replace(curd, ingredients=("milk", "sucralose"), contains_sweeteners=True)
    assert _alerts(p, m, cfg) == [("artificial_sweetener", ["sucralose"])]


def test_sweetener_flag_without_ingredients_alerts_and_rest_unknown(cfg):
    p = Product(name="x", contains_sweeteners=True)
    assert _codes(custom_alert_reasons(p, PROBE, cfg)) == [
        ("custom_alert", Status.CAUTION, {"alert": "artificial_sweetener", "ingredients": []}),
        (
            "custom_alert_unknown",
            Status.UNKNOWN,
            {"alerts": ["palm_oil", "maida", "added_sugar", "msg"]},
        ),
    ]


def test_sweetener_flag_ignored_when_alert_is_off(curd, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("msg",))
    assert custom_alert_reasons(replace(curd, contains_sweeteners=True), m, cfg) == []


# --- more label terms (Ruling P7 should-fix) ---------------------------------------------


@pytest.mark.parametrize(
    ("ingredients", "hits"),
    [
        (("sugar", "milk solids", "contains artificial sweetener"), ["artificial sweetener"]),
        (
            ("CONTAINS ARTIFICIAL SWEETENER. NOT RECOMMENDED FOR CHILDREN",),
            ["artificial sweetener"],
        ),
        (
            ("milk solids", "artificial sweetening agents (ins 950, ins 955)"),
            ["artificial sweetening agent", "ins950", "ins955"],
        ),
        (("non-nutritive sweetener (sucralose)",), ["non nutritive sweetener", "sucralose"]),
        (("cocoa", "sweeteners (Ace-K, aspartame)"), ["ace k", "aspartame"]),
        (("Acesulfame", "water"), ["acesulfame"]),
        (("Acesulfame-K", "water"), ["acesulfame k"]),
        (("कोको", "एस्पार्टेम"), ["एस्पार्टेम"]),
        (("दूध", "सुक्रालोज"), ["सुक्रालोज"]),
        (("सैकरीन",), ["सैकरीन"]),
        (("सैक्रीन",), ["सैक्रीन"]),
        (("एसेसल्फेम पोटैशियम",), ["एसेसल्फेम"]),
        (("इसमें कृत्रिम स्वीटनर है",), ["कृत्रिम स्वीटनर"]),
        (("इसमें कृत्रिम मिठास मिलाई गई है",), ["कृत्रिम मिठास"]),
        (("यात कृत्रिम गोडवा आहे",), ["कृत्रिम गोडवा"]),
    ],
)
def test_more_artificial_sweetener_terms(curd, cfg, ingredients, hits):
    m = Member(id="x", name="X", age=30, custom_alerts=("artificial_sweetener",))
    assert _alerts(replace(curd, ingredients=ingredients), m, cfg) == [
        ("artificial_sweetener", hits)
    ]


@pytest.mark.parametrize(
    ("ingredients", "hits"),
    [
        (("noodles", "tastemaker (salt, Ajinomoto)"), ["ajinomoto"]),
        (("seasoning (aji-no-moto)",), ["aji no moto"]),
        (("नमक", "अजीनोमोटो"), ["अजीनोमोटो"]),
        (("अजिनोमोटो",), ["अजिनोमोटो"]),
        (("flavour enhancer (Monosodium L-glutamate)",), ["monosodium l glutamate"]),
        (("स्वाद वर्धक (मोनोसोडियम ग्लूटामेट)",), ["मोनोसोडियम ग्लूटामेट"]),
    ],
)
def test_more_msg_terms(curd, cfg, ingredients, hits):
    m = Member(id="x", name="X", age=30, custom_alerts=("msg",))
    assert _alerts(replace(curd, ingredients=ingredients), m, cfg) == [("msg", hits)]


@pytest.mark.parametrize(
    ("ingredients", "hits"),
    [
        (("All-purpose flour", "sugar"), ["all purpose flour"]),
        (("white flour", "yeast"), ["white flour"]),
        (("मैद्याचे पीठ", "साखर"), ["मैद्याचे पीठ"]),
    ],
)
def test_more_maida_terms(curd, cfg, ingredients, hits):
    m = Member(id="x", name="X", age=30, custom_alerts=("maida",))
    assert _alerts(replace(curd, ingredients=ingredients), m, cfg) == [("maida", hits)]


def test_wheat_flour_refined_in_brackets_is_a_known_gap(curd, cfg):
    # Documented limitation (ingredients.yaml): the bracket splits "wheat flour" from
    # "refined", so "Wheat flour (refined)" does not raise the maida alert.
    m = Member(id="x", name="X", age=30, custom_alerts=("maida",))
    p = replace(curd, ingredients=("Wheat flour (refined)",))
    assert custom_alert_reasons(p, m, cfg) == []


@pytest.mark.parametrize(
    "ingredients",
    [("palm heart",), ("Palm hearts", "brine"), ("hearts of palm",), ("heart of palm",)],
)
def test_palm_heart_is_not_a_palm_oil_alert(curd, cfg, ingredients):
    m = Member(id="x", name="X", age=30, custom_alerts=("palm_oil",))
    assert custom_alert_reasons(replace(curd, ingredients=ingredients), m, cfg) == []


def test_palm_heart_with_palm_oil_still_alerts(curd, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("palm_oil",))
    p = replace(curd, ingredients=("hearts of palm", "palm oil"))
    assert _alerts(p, m, cfg) == [("palm_oil", ["palm oil"])]


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
    assert analyze(curd, [ALL_ALERTS], cfg).verdicts[0].status == Status.OK


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

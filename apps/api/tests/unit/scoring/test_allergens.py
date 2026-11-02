from dataclasses import replace

import pytest

from app.scoring.allergens import allergen_reasons, detect_allergens
from app.scoring.models import AllergenState, Status


def test_biscuit_contains_milk_and_gluten_may_contain_soy(sf_biscuit, cfg):
    d = detect_allergens(sf_biscuit, cfg)
    assert d["milk"] == AllergenState.CONTAINS and d["gluten"] == AllergenState.CONTAINS
    assert d["soy"] == AllergenState.MAY_CONTAIN  # bare "ins 322"


def test_may_contain_statement(curd, cfg):
    p = replace(curd, may_contain_statement="May contain traces of nuts and peanuts")
    d = detect_allergens(p, cfg)
    assert d["peanut"] == AllergenState.MAY_CONTAIN and d["tree_nut"] == AllergenState.MAY_CONTAIN


def test_coconut_milk_is_not_milk(curd, cfg):
    assert "milk" not in detect_allergens(replace(curd, ingredients=("coconut milk", "sugar")), cfg)


def test_hindi_peanut(curd, cfg):
    assert (
        detect_allergens(replace(curd, ingredients=("मूंगफली", "नमक")), cfg)["peanut"]
        == AllergenState.CONTAINS
    )


def test_custom_allergen_matched_literally(curd, cfg, peanut_allergic):
    p = replace(curd, ingredients=("kiwi pulp", "sugar"))
    m = replace(peanut_allergic, allergens=("kiwi",))
    assert [r.code for r in allergen_reasons(p, m, cfg)] == ["allergen_contains"]


def test_unknown_ingredients_never_ok(no_ingredients, cfg, peanut_allergic):
    rs = allergen_reasons(no_ingredients, peanut_allergic, cfg)
    assert [(r.code, r.severity) for r in rs] == [("allergen_unknown", Status.UNKNOWN)]


def test_low_confidence_is_unknown(namkeen, cfg, milk_allergic_child):
    rs = allergen_reasons(replace(namkeen, extraction_confidence=0.5), milk_allergic_child, cfg)
    assert rs[0].code == "allergen_unknown"


def test_peanut_allergy_on_namkeen(namkeen, cfg, peanut_allergic):
    assert allergen_reasons(namkeen, peanut_allergic, cfg)[0].severity == Status.AVOID


def test_member_allergen_key_case_insensitive(namkeen, cfg, peanut_allergic):
    m = replace(peanut_allergic, allergens=("Peanut",))
    assert allergen_reasons(namkeen, m, cfg)[0].params == {"allergen": "peanut"}


def _codes(p, m, cfg):
    return [r.code for r in allergen_reasons(p, m, cfg)]


@pytest.mark.parametrize(
    "ings",
    [
        ("coconut", "milk solids"),
        ("almond", "milk"),
        ("roasted peanut", "butter"),
        ("sugar", "cocoa", "butter"),
    ],
)
def test_exclude_phrase_does_not_span_items(curd, cfg, milk_allergic_child, ings):
    assert _codes(replace(curd, ingredients=ings), milk_allergic_child, cfg) == [
        "allergen_contains"
    ]


@pytest.mark.parametrize(
    "key,statement",
    [
        ("gluten", "Contains: Gluten"),
        ("tree_nut", "CONTAINS: TREE NUTS"),
        ("crustacean", "Contains: Crustaceans"),
        ("crustacean", "Contains: Shellfish"),
        ("sulphite", "Contains: Sulphur dioxide"),
    ],
)
def test_allergen_statement_canonical_names(oats, cfg, peanut_allergic, key, statement):
    p = replace(oats, ingredients=("starch",), allergen_statement=statement)
    m = replace(peanut_allergic, allergens=(key,))
    assert _codes(p, m, cfg) == ["allergen_contains"]


def test_may_contain_gluten_statement(oats, cfg, peanut_allergic):
    p = replace(oats, ingredients=("starch",), may_contain_statement="May contain gluten")
    m = replace(peanut_allergic, allergens=("gluten",))
    assert _codes(p, m, cfg) == ["allergen_may_contain"]


@pytest.mark.parametrize("ings", [("  ",), ("",), ("", " ")])
def test_blank_ingredients_are_unknown(curd, cfg, peanut_allergic, ings):
    assert _codes(replace(curd, ingredients=ings), peanut_allergic, cfg) == ["allergen_unknown"]


@pytest.mark.parametrize(
    "key,ings",
    [
        ("tree nut", ("cashew",)),
        ("tree-nut", ("cashew",)),
        ("Tree Nuts", ("cashew",)),
        ("dairy", ("milk solids",)),
        ("shellfish", ("prawn",)),
        ("wheat", ("maida",)),
        ("groundnut", ("peanuts",)),
    ],
)
def test_member_key_variants(curd, cfg, peanut_allergic, key, ings):
    m = replace(peanut_allergic, allergens=(key,))
    assert _codes(replace(curd, ingredients=ings), m, cfg) == ["allergen_contains"]


@pytest.mark.parametrize(
    "key,statement", [("tree_nut", "Contains: nuts"), ("soy", "Contains: lecithin")]
)
def test_possible_term_in_allergen_statement_is_may_contain(
    oats, cfg, peanut_allergic, key, statement
):
    p = replace(oats, ingredients=("starch",), allergen_statement=statement)
    m = replace(peanut_allergic, allergens=(key,))
    assert _codes(p, m, cfg) == ["allergen_may_contain"]


@pytest.mark.parametrize("ings", [("albumen", "sugar"), ("अंडे", "नमक")])
def test_egg_albumen_and_hindi_plural(curd, cfg, peanut_allergic, ings):
    m = replace(peanut_allergic, allergens=("egg",))
    assert _codes(replace(curd, ingredients=ings), m, cfg) == ["allergen_contains"]


def test_may_contain_statement_without_ingredients(no_ingredients, cfg, peanut_allergic):
    p = replace(no_ingredients, may_contain_statement="may contain peanuts")
    assert [r.code for r in allergen_reasons(p, peanut_allergic, cfg)] == [
        "allergen_may_contain",
        "allergen_unknown",
    ]


def _reasons(p, m, cfg):
    return [(r.code, r.severity, r.params.get("allergen")) for r in allergen_reasons(p, m, cfg)]


# --- Final fix wave A1: separators + partial excludes (R19) ---


@pytest.mark.parametrize(
    "ings",
    [
        ("coconut & milk solids",),
        ("sugar, desiccated coconut. milk powder",),
        ("peanut & butter",),
    ],
)
def test_new_separators_milk_contains(curd, cfg, ings):
    assert detect_allergens(replace(curd, ingredients=ings), cfg)["milk"] == AllergenState.CONTAINS


@pytest.mark.parametrize("ings", [("almond milk chocolate",), ("sugar", "peanut butter cookies")])
def test_partial_exclude_is_may_contain(curd, cfg, ings):
    assert (
        detect_allergens(replace(curd, ingredients=ings), cfg)["milk"] == AllergenState.MAY_CONTAIN
    )


@pytest.mark.parametrize("ings", [("coconut milk",), ("Coconut Milk (60%)", "water")])
def test_exact_exclude_segment_stays_excluded(curd, cfg, ings):
    assert "milk" not in detect_allergens(replace(curd, ingredients=ings), cfg)


def test_partial_exclude_without_trigger_word_is_ignored(curd, cfg):
    # "coconut" is a defensive tree_nut exclude with no tree_nut term inside it.
    d = detect_allergens(replace(curd, ingredients=("desiccated coconut", "sugar")), cfg)
    assert "tree_nut" not in d


# --- A3: Hindi/Marathi and English term additions ---


@pytest.mark.parametrize(
    "key,ing",
    [
        ("milk", "dairy whitener"),
        ("milk", "mawa"),
        ("milk", "lactitol"),
        ("milk", "ins966"),
        ("milk", "INS 966"),
        ("milk", "milk fat"),
        ("milk", "butter oil"),
        ("milk", "मक्खन"),
        ("milk", "मलाई"),
        ("milk", "खोया"),
        ("milk", "दूध पावडर"),
        ("peanut", "शेंगदाणा"),
        ("peanut", "मूँगफली"),
        ("gluten", "rawa"),
        ("gluten", "vermicelli"),
        ("gluten", "semiya"),
        ("gluten", "couscous"),
        ("gluten", "आटा"),
        ("gluten", "सूजी"),
        ("gluten", "गहू"),
        ("gluten", "गेहूँ"),
        ("soy", "सोयाबीन"),
        ("soy", "tofu"),
        ("egg", "ins1105"),
        ("egg", "lysozyme (INS 1105)"),
        ("tree_nut", "cashewnut"),
        ("tree_nut", "cashew nut"),
        ("tree_nut", "chironji"),
        ("tree_nut", "charoli"),
        ("tree_nut", "chilgoza"),
        ("tree_nut", "pine nuts"),
        ("tree_nut", "brazil nut"),
        ("tree_nut", "काजू"),
        ("tree_nut", "बादाम"),
        ("tree_nut", "पिस्ता"),
        ("tree_nut", "अखरोट"),
        ("sesame", "तिल"),
        ("sesame", "tahini"),
        ("fish", "salmon"),
        ("fish", "mackerel"),
        ("fish", "मछली"),
        ("crustacean", "झींगा"),
        ("mustard", "सरसों"),
        ("mustard", "राई"),
    ],
)
def test_added_terms_contain(curd, cfg, peanut_allergic, key, ing):
    p = replace(curd, ingredients=(ing, "नमक"))
    m = replace(peanut_allergic, allergens=(key,))
    assert _reasons(p, m, cfg) == [("allergen_contains", Status.AVOID, key)]


@pytest.mark.parametrize(
    "field,text",
    [
        ("may_contain_statement", "May contain traces of nuts"),
        ("allergen_statement", "Contains: Nuts"),
    ],
)
def test_generic_nuts_is_peanut_may_contain(oats, cfg, field, text):
    p = replace(oats, ingredients=("starch",), **{field: text})
    assert detect_allergens(p, cfg)["peanut"] == AllergenState.MAY_CONTAIN


def test_dry_fruits_is_tree_nut_may_contain(oats, cfg):
    p = replace(oats, ingredients=("sugar", "dry fruits (5%)"))
    assert detect_allergens(p, cfg)["tree_nut"] == AllergenState.MAY_CONTAIN


# --- A4: free-text member keys (R20) ---


@pytest.mark.parametrize(
    "key,ings,allergen",
    [
        ("peanut allergy", ("peanuts",), "peanut"),
        ("Peanut Allergies", ("peanuts",), "peanut"),
        ("nut", ("almonds",), "tree_nut"),
        ("nut", ("peanuts",), "peanut"),
        ("nuts", ("peanuts",), "peanut"),
        ("celiac", ("wheat flour",), "gluten"),
        ("Coeliac disease", ("wheat flour",), "gluten"),
        ("cow's milk", ("milk solids",), "milk"),
        ("cows milk", ("milk solids",), "milk"),
        ("lactose intolerance", ("milk solids",), "milk"),
        ("milk products", ("milk solids",), "milk"),
        ("dairy products", ("milk solids",), "milk"),
        ("prawns", ("prawn",), "crustacean"),
        ("seafood", ("shrimp",), "crustacean"),
        ("seafood", ("tuna",), "fish"),
        ("sesame seeds", ("sesame oil",), "sesame"),
        ("peanut butter", ("roasted peanuts",), "peanut"),
        ("sulphites", ("ins220",), "sulphite"),
        ("egg white", ("egg powder",), "egg"),
        ("kiwi", ("kiwi pulp",), "kiwi"),
        ("kiwis", ("kiwi pulp",), "kiwi"),
    ],
)
def test_free_text_member_keys(curd, cfg, peanut_allergic, key, ings, allergen):
    m = replace(peanut_allergic, allergens=(key,))
    assert _reasons(replace(curd, ingredients=ings), m, cfg) == [
        ("allergen_contains", Status.AVOID, allergen)
    ]


def test_unrecognised_key_is_unknown(curd, cfg, peanut_allergic):
    m = replace(peanut_allergic, allergens=("kiwi fruit",))
    p = replace(curd, ingredients=("kiwi pulp", "sugar"))
    assert _reasons(p, m, cfg) == [("allergen_unrecognised", Status.UNKNOWN, "kiwi_fruit")]


def test_unrecognised_key_literal_match_is_contains(curd, cfg, peanut_allergic):
    m = replace(peanut_allergic, allergens=("kiwi fruit",))
    p = replace(curd, ingredients=("kiwi fruit pulp", "sugar"))
    assert _reasons(p, m, cfg) == [("allergen_contains", Status.AVOID, "kiwi_fruit")]


def test_word_fallback_keeps_literal_phrase(curd, cfg, peanut_allergic):
    m = replace(peanut_allergic, allergens=("coconut milk",))
    p = replace(curd, ingredients=("coconut milk", "water"))
    assert _reasons(p, m, cfg) == [("allergen_contains", Status.AVOID, "coconut_milk")]


def test_nut_key_report_lists_both(curd, cfg):
    d = detect_allergens(replace(curd, ingredients=("almonds", "peanuts")), cfg, ["nut allergy"])
    assert d["tree_nut"] == AllergenState.CONTAINS and d["peanut"] == AllergenState.CONTAINS
    assert "nut" not in d and "nut_allergy" not in d


# --- A5: placeholder ingredient text (R21) ---


@pytest.mark.parametrize(
    "ings", [("-",), (".",), ("*",), ("N/A",), ("see pack",), ("Ingredients:",)]
)
def test_placeholder_ingredients_are_unknown(curd, cfg, peanut_allergic, ings):
    assert _codes(replace(curd, ingredients=ings), peanut_allergic, cfg) == ["allergen_unknown"]


# --- A6: may-contain hit with unknown ingredients still reports unknown ---


def test_may_contain_without_ingredients_also_unknown(no_ingredients, cfg, peanut_allergic):
    caution_cfg = replace(
        cfg, thresholds={**cfg.thresholds, "allergen_may_contain_status": "caution"}
    )
    p = replace(no_ingredients, may_contain_statement="may contain peanuts")
    assert _reasons(p, peanut_allergic, caution_cfg) == [
        ("allergen_may_contain", Status.CAUTION, "peanut"),
        ("allergen_unknown", Status.UNKNOWN, "peanut"),
    ]


# --- R30: generic "nuts" is peanut may-contain; named tree nuts are not ---


@pytest.mark.parametrize(
    "field,text",
    [
        ("allergen_statement", "Contains: Nuts"),
        ("may_contain_statement", "May contain traces of nuts"),
    ],
)
def test_generic_nuts_still_peanut_may_contain(oats, cfg, peanut_allergic, field, text):
    p = replace(oats, ingredients=("starch",), **{field: text})
    assert _reasons(p, peanut_allergic, cfg) == [("allergen_may_contain", Status.AVOID, "peanut")]


@pytest.mark.parametrize(
    "ings,statement",
    [
        (("cashew nuts", "sugar"), None),
        (("cashew nut",), None),
        (("roasted cashew nuts (10%)", "salt"), None),
        (("mixed tree nuts", "sugar"), None),
        (("sugar",), "May contain tree nuts"),
    ],
)
def test_named_tree_nuts_are_not_peanut(oats, cfg, peanut_allergic, ings, statement):
    p = replace(oats, ingredients=ings, may_contain_statement=statement)
    assert "peanut" not in detect_allergens(p, cfg)
    assert _reasons(p, peanut_allergic, cfg) == []

import pytest

from app.scoring.ingredients import (
    _pattern,
    excluded_hits,
    find_terms,
    has_ingredient_content,
    modifier_excludes,
    normalize,
)


def test_normalize_ins_codes():
    n = normalize("Emulsifier (INS 322), E-471, raising agent (ins 500(ii)), stabiliser (412)")
    assert {"ins322", "ins471", "ins500", "ins412"} <= set(n.split())


def test_word_boundary_and_plural():
    assert find_terms(["roasted peanuts"], ["peanut"]) == ["peanut"]
    assert find_terms(["eggplant"], ["egg"]) == []


def test_exclude_phrases():
    assert find_terms(["cocoa butter", "sugar"], ["butter"], exclude=["cocoa butter"]) == []


def test_devanagari_terms():
    assert find_terms(["मूंगफली", "चीनी"], ["मूंगफली", "चीनी"]) == ["चीनी", "मूंगफली"]


def test_devanagari_no_match_inside_longer_word():
    assert find_terms(["दूधवाला"], ["दूध"]) == []
    assert find_terms(["दूध, चीनी"], ["दूध"]) == ["दूध"]


def test_longest_match_consumes_text():
    assert find_terms(["liquid glucose", "salt"], ["liquid glucose", "glucose"]) == [
        "liquid glucose"
    ]
    assert find_terms(["onion powder"], ["onion", "onion powder"]) == ["onion powder"]


MILK = ["milk", "milk powder", "milk solids", "butter", "cream"]
MILK_EX = ["coconut milk", "almond milk", "cocoa butter", "peanut butter", "nut butter"]


def test_excludes_do_not_span_ingredient_boundaries():
    for texts in (
        ["desiccated coconut", "milk powder"],
        ["Desiccated Coconut, Milk Solids"],
        ["Almond", "Milk"],
        ["Cocoa", "Butter"],
        ["Peanut", "Butter"],
    ):
        assert find_terms(texts, MILK, MILK_EX), texts


def test_in_segment_exclude_still_works():
    assert find_terms(["coconut milk"], MILK, MILK_EX) == []


def test_segments_split_on_brackets_and_slash():
    assert find_terms(["coconut (milk)"], MILK, MILK_EX) == ["milk"]
    assert find_terms(["coconut/milk"], MILK, MILK_EX) == ["milk"]


def test_ins_code_formats():
    for text in ("E 220", "INS. 220", "ins: 220", "E-220", "INS 220", "e220", "Preservative (220)"):
        assert "ins220" in normalize(text).split(), text
    n = normalize("Preservatives (220, 223), Emulsifiers (322, 471)").split()
    assert {"ins220", "ins223", "ins322", "ins471"} <= set(n)


def test_ordinary_numbers_untouched():
    for text in ("vitamin e 1000 iu", "500 g", "contains 100% juice", "Vitamin E 400 mg"):
        assert not any(w.startswith("ins") for w in normalize(text).split()), text


def test_sulphite_code_list():
    sulphite = ["ins220", "ins221", "ins222", "ins223", "ins224"]
    assert find_terms(["Preservatives (220, 223)"], sulphite) == ["ins220", "ins223"]


def test_devanagari_nukta_insensitive():
    assert find_terms(["प्याज़"], ["प्याज"]) == ["प्याज"]
    assert find_terms(["प्याज"], ["प्याज़"]) == ["प्याज़"]
    assert find_terms(["गुड़"], ["गुड़"]) == ["गुड़"]


def test_ies_plurals():
    assert find_terms(["anchovies"], ["anchovy"]) == ["anchovy"]
    assert find_terms(["dried berries"], ["berry"]) == ["berry"]
    assert find_terms(["candies"], ["candy"]) == ["candy"]
    assert find_terms(["anchovy"], ["anchovy"]) == ["anchovy"]


def test_zero_width_chars_stripped():
    assert find_terms(["pea‍nut"], ["peanut"]) == ["peanut"]


# --- Final fix wave A1: extra segment separators + partial excludes (R19) ---


@pytest.mark.parametrize(
    "texts",
    [
        ["coconut & milk solids"],
        ["sugar, desiccated coconut. milk powder"],
        ["peanut & butter"],
        ["almond + milk"],
        ["cocoa and butter"],
    ],
)
def test_new_separators_split_excludes(texts):
    assert find_terms(texts, MILK, MILK_EX), texts


def test_dot_without_space_is_not_a_separator():
    assert "ins220" in normalize("INS. 220").split()
    assert find_terms(["salt 2.5%"], ["salt"]) == ["salt"]


def test_and_inside_word_is_not_a_separator():
    assert find_terms(["sandalwood candy"], ["candy"]) == ["candy"]
    assert find_terms(["almond milk"], MILK, MILK_EX) == []


def test_excluded_hits_reports_partial_segments_only():
    assert excluded_hits(["almond milk chocolate"], MILK_EX) == ["almond milk"]
    assert excluded_hits(["peanut butter cookies"], MILK_EX) == ["peanut butter"]
    assert excluded_hits(["coconut milk", "sugar"], MILK_EX) == []
    assert excluded_hits(["Coconut Milk (60%)"], MILK_EX) == []
    assert excluded_hits(["sugar"], MILK_EX) == []


def test_modifier_excludes_need_trailing_words():
    # R30: an exclude phrase only hides a trigger when it modifies a following noun.
    assert modifier_excludes(["almond milk chocolate"], MILK_EX) == ["almond milk"]
    assert modifier_excludes(["peanut butter cookies"], MILK_EX) == ["peanut butter"]
    assert modifier_excludes(["light coconut milk", "coconut milk"], MILK_EX) == []
    nuts_ex = ["tree nuts", "cashew nuts", "mixed tree nuts"]
    assert modifier_excludes(["roasted cashew nuts", "mixed tree nuts"], nuts_ex) == []
    assert modifier_excludes(["may contain tree nuts"], nuts_ex) == []
    assert modifier_excludes(["tree nuts paste"], nuts_ex) == ["tree nuts"]


# --- A2: chandrabindu folds to anusvara ---


def test_chandrabindu_matches_anusvara():
    assert find_terms(["मूँगफली"], ["मूंगफली"]) == ["मूंगफली"]
    assert find_terms(["मूंगफली"], ["मूँगफली"]) == ["मूँगफली"]
    assert find_terms(["गेहूँ का आटा"], ["गेहूं"]) == ["गेहूं"]
    assert find_terms(["गेहूं"], ["गेहूँ"]) == ["गेहूँ"]


# --- A5: placeholder ingredient text (R21) ---


@pytest.mark.parametrize(
    "texts",
    [
        ("-",),
        (".",),
        ("*",),
        ("N/A",),
        ("n.a.",),
        ("NA",),
        ("nil",),
        ("None",),
        ("Not Available",),
        ("see pack",),
        ("See Package",),
        ("Ingredients:",),
        ("Ingredient",),
        ("", "-"),
        ("x",),
    ],
)
def test_placeholder_ingredients_have_no_content(texts):
    assert not has_ingredient_content(texts)


@pytest.mark.parametrize("texts", [("water",), ("Ingredients: water",), ("दूध",), ("-", "salt")])
def test_real_ingredients_have_content(texts):
    assert has_ingredient_content(texts)


# --- A7: compiled-pattern builder is cached ---


def test_pattern_builder_is_lru_cached():
    assert hasattr(_pattern, "cache_info")

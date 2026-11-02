from dataclasses import replace

import pytest

from app.scoring.diet import diet_reasons, diet_violations, veg_mark_mismatch
from app.scoring.models import Diet, Product, Status


def test_namkeen_not_jain(namkeen, cfg):
    assert diet_violations(namkeen, cfg)[Diet.JAIN] == ("garlic powder", "onion powder")


def test_curd_not_vegan(curd, cfg):
    assert diet_violations(curd, cfg)[Diet.VEGAN] == ("milk",)


def test_non_veg_always_empty(curd, cfg):
    v = diet_violations(curd, cfg)
    assert v[Diet.NON_VEG] == ()
    assert set(v) == set(Diet)


def test_gelatin_breaks_veg_mark(curd, cfg):
    p = replace(curd, ingredients=("milk", "gelatin"), veg_mark="veg")
    assert veg_mark_mismatch(p, cfg) is True


def test_jain_member_avoids_namkeen(namkeen, cfg, jain_adult):
    assert diet_reasons(namkeen, jain_adult, cfg)[0].severity == Status.AVOID


def test_unknown_ingredients_with_veg_mark_ok_for_veg(no_ingredients, cfg, diabetic_adult):
    assert diet_reasons(replace(no_ingredients, veg_mark="veg"), diabetic_adult, cfg) == []


def test_eggetarian_veg_mark_exception(no_ingredients, cfg, diabetic_adult):
    member = replace(diabetic_adult, diet=Diet.EGGETARIAN)
    assert diet_reasons(replace(no_ingredients, veg_mark="veg"), member, cfg) == []


def _m(base, diet):
    return replace(base, diet=diet)


def test_brown_dot_tuna_avoid_for_veg(cfg, diabetic_adult):
    p = Product(name="t", ingredients=("tuna", "salt"), veg_mark="non_veg")
    r = diet_reasons(p, diabetic_adult, cfg)
    assert r[0].severity == Status.AVOID and r[0].params["mark"] == "non_veg"


def test_brown_dot_salmon_avoid_for_jain(cfg, jain_adult):
    p = Product(name="t", ingredients=("salmon",), veg_mark="non_veg")
    assert diet_reasons(p, jain_adult, cfg)[0].severity == Status.AVOID


def test_brown_dot_no_term_still_avoid_for_vegan(cfg, vegan_adult):
    p = Product(name="t", ingredients=("wheat flour",), veg_mark="non_veg")
    r = diet_reasons(p, vegan_adult, cfg)
    assert r[0].severity == Status.AVOID
    assert r[0].params == {"diet": "vegan", "ingredients": [], "mark": "non_veg"}


def test_brown_dot_unknown_ingredients_avoid_for_veg(cfg, diabetic_adult, no_ingredients):
    p = replace(no_ingredients, veg_mark="non_veg")
    assert diet_reasons(p, diabetic_adult, cfg)[0].severity == Status.AVOID


def test_brown_dot_eggetarian_no_term_unknown(cfg, diabetic_adult):
    p = Product(name="t", ingredients=("wheat flour",), veg_mark="non_veg")
    r = diet_reasons(p, _m(diabetic_adult, Diet.EGGETARIAN), cfg)
    assert [(x.code, x.severity) for x in r] == [("diet_unknown", Status.UNKNOWN)]
    assert r[0].params == {"diet": "eggetarian", "mark": "non_veg"}


def test_brown_dot_eggetarian_with_chicken_avoid(cfg, diabetic_adult):
    p = Product(name="t", ingredients=("chicken",), veg_mark="non_veg")
    assert diet_reasons(p, _m(diabetic_adult, Diet.EGGETARIAN), cfg)[0].severity == Status.AVOID


def test_brown_dot_non_veg_member_unaffected(cfg, diabetic_adult):
    p = Product(name="t", ingredients=("tuna",), veg_mark="non_veg")
    assert diet_reasons(p, _m(diabetic_adult, Diet.NON_VEG), cfg) == []


def test_allergen_statement_egg_milk_violates_veg(cfg):
    p = Product(
        name="t", ingredients=("wheat flour", "sugar"), allergen_statement="Contains: Egg, Milk"
    )
    assert diet_violations(p, cfg)[Diet.VEG] == ("egg",)


def test_allergen_statement_milk_violates_vegan(cfg):
    p = Product(name="t", ingredients=("wheat flour", "sugar"), allergen_statement="Contains milk")
    assert diet_violations(p, cfg)[Diet.VEGAN] == ("milk",)


def test_may_contain_statement_not_searched(cfg):
    p = Product(name="t", ingredients=("wheat flour",), may_contain_statement="May contain milk")
    assert diet_violations(p, cfg)[Diet.VEGAN] == ()


def test_statement_alone_does_not_make_ingredients_known(cfg, vegan_adult):
    p = Product(name="t", allergen_statement="Contains wheat")
    assert diet_reasons(p, vegan_adult, cfg)[0].code == "diet_unknown"


def test_eggetarian_allows_egg(cfg, diabetic_adult):
    p = Product(name="t", ingredients=("egg", "flour"))
    assert diet_reasons(p, _m(diabetic_adult, Diet.EGGETARIAN), cfg) == []


def test_eggetarian_chicken_avoid(cfg, diabetic_adult):
    p = Product(name="t", ingredients=("chicken",))
    assert diet_reasons(p, _m(diabetic_adult, Diet.EGGETARIAN), cfg)[0].severity == Status.AVOID


def test_low_confidence_violation_still_avoid(cfg, vegan_adult):
    p = Product(name="t", ingredients=("milk",), extraction_confidence=0.1)
    r = diet_reasons(p, vegan_adult, cfg)
    assert r[0].code == "diet_violation" and r[0].severity == Status.AVOID


def test_unknown_ingredients_unknown_for_vegan(no_ingredients, cfg, vegan_adult):
    assert diet_reasons(no_ingredients, vegan_adult, cfg)[0].code == "diet_unknown"


# --- final safety review: term-list regressions -------------------------------------------
_NEW_NON_VEG = [
    "tuna",
    "salmon",
    "mackerel",
    "sardine",
    "squid",
    "octopus",
    "lobster",
    "oyster sauce",
    "cod liver oil",
    "collagen",
    "seafood",
    "keema",
    "animal fat",
    "bacon",
    "ham",
    "turkey",
    "beef extract",
    "ins441",
    "ins542",
    "ins920",
    "चिकन",
    "मछली",
    "मांस",
    "झींगा",
]


@pytest.mark.parametrize("term", _NEW_NON_VEG)
def test_veg_member_avoids_new_non_veg_terms(term, no_ingredients, cfg, diabetic_adult):
    p = replace(no_ingredients, ingredients=("wheat flour", term))
    reasons = diet_reasons(p, replace(diabetic_adult, diet=Diet.VEG), cfg)
    assert reasons and reasons[0].severity == Status.AVOID


@pytest.mark.parametrize("term", ["khoa", "दूध", "dairy whitener", "mawa", "मक्खन", "milk fat"])
def test_vegan_avoids_dairy_terms(term, no_ingredients, cfg, vegan_adult):
    p = replace(no_ingredients, ingredients=("sugar", term))
    reasons = diet_reasons(p, vegan_adult, cfg)
    assert reasons and reasons[0].severity == Status.AVOID


@pytest.mark.parametrize(
    "term", ["aloo", "kanda", "आलू", "mushroom", "lehsun", "yeast", "अदरक", "शकरकंद"]
)
def test_jain_avoids_new_exclusions(term, no_ingredients, cfg, jain_adult):
    p = replace(no_ingredients, ingredients=("rice", term))
    reasons = diet_reasons(p, jain_adult, cfg)
    assert reasons and reasons[0].severity == Status.AVOID


def test_veg_avoids_ins1105(no_ingredients, cfg, diabetic_adult):
    p = replace(no_ingredients, ingredients=("flour", "ins 1105"))
    assert diet_reasons(p, replace(diabetic_adult, diet=Diet.VEG), cfg)[0].severity == Status.AVOID


@pytest.mark.parametrize("text", ["graham flour", "steam cooked rice", "tomato", "chocolate"])
def test_new_non_veg_terms_do_not_overmatch(text, no_ingredients, cfg, diabetic_adult):
    p = replace(no_ingredients, ingredients=(text,))
    reasons = diet_reasons(p, replace(diabetic_adult, diet=Diet.VEG), cfg)
    assert not any(r.code == "diet_violation" for r in reasons)

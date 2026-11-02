from dataclasses import replace

from app.scoring.diet import diet_reasons, diet_violations, veg_mark_mismatch
from app.scoring.models import Diet, Status


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
    member = replace(diabetic_adult, diet=Diet.VEG)
    assert diet_reasons(replace(no_ingredients, veg_mark="veg"), member, cfg) == []
    assert diet_reasons(replace(no_ingredients, veg_mark="veg"), diabetic_adult, cfg) == []


def test_unknown_ingredients_unknown_for_vegan(no_ingredients, cfg, vegan_adult):
    assert diet_reasons(no_ingredients, vegan_adult, cfg)[0].code == "diet_unknown"

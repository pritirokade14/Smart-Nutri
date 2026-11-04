"""Plan 9 Task 7 (P9-R10): supplements are not graded, still checked, never suggested.

- No Nutri-Score grade (`not_scored_supplement`); allergens, diet, claims, conditions and
  protein facts still run.
- Member reasons from `thresholds.yaml` `supplements` (PENDING CLINICIAN REVIEW): under 2
  `supplement_infant` (avoid), 2 to 17 `supplement_child` (caution), unknown age the existing
  `age_unknown` (unknown). Adults get a status from the other rules only.
- Detected only from the category the user picks or from Open Food Facts tags, never from
  the LLM: the extraction schema and the normaliser never propose it.
"""

from dataclasses import replace
from typing import get_args

import pytest

from app.features.products.off_mapping import SUPPLEMENT_TAGS, off_to_product
from app.features.scans.normalize import to_draft
from app.features.scans.schemas import NutritionExtraction
from app.scoring import Category, Diet, Member, Nutrients, Product, Status, analyze
from app.scoring.models import ClaimVerdict
from tests.unit.scans.test_normalize import ex


def _whey(**kw):
    base = Product(
        name="Whey",
        category=Category.SUPPLEMENT,
        per_100g=Nutrients(
            energy_kcal=400,
            protein_g=80,
            carbs_g=8,
            sugars_g=4,
            fat_g=6,
            sat_fat_g=3,
            fiber_g=1,
            salt_g=0.5,
        ),
        serving_size_g=30,
        ingredients=("whey protein concentrate", "cocoa powder", "sucralose"),
    )
    return replace(base, **kw)


def _verdict(product, member, cfg):
    return analyze(product, [member], cfg).verdicts[0]


def _codes(verdict):
    return [(r.code, r.severity) for r in verdict.reasons]


ADULT = Member(id="a", name="A", age=30)


def test_supplement_has_no_grade_reason_not_scored(cfg):
    ns = analyze(_whey(), [], cfg).report.nutriscore
    assert (ns.grade, ns.points, ns.reason) == (None, None, "not_scored_supplement")


def test_same_values_as_food_are_graded(cfg):
    assert analyze(_whey(category=Category.GENERAL), [], cfg).report.nutriscore.grade is not None


def test_whey_flags_milk_for_milk_allergic_member(cfg):
    m = Member(id="m", name="M", age=30, allergens=("milk",))
    v = _verdict(_whey(), m, cfg)
    assert v.status == Status.AVOID
    assert ("allergen_contains", Status.AVOID) in _codes(v)


def test_vegan_diet_still_checked(cfg):
    v = _verdict(_whey(), Member(id="v", name="V", age=30, diet=Diet.VEGAN), cfg)
    assert v.status == Status.AVOID and any(r.code == "diet_violation" for r in v.reasons)


@pytest.mark.parametrize("age", [2, 9, 13, 17])
def test_supplement_child_caution(cfg, age):
    v = _verdict(_whey(), Member(id="c", name="C", age=age), cfg)
    assert ("supplement_child", Status.CAUTION) in _codes(v)
    assert v.status.rank >= Status.CAUTION.rank


def test_supplement_teen_caution(cfg):
    v = _verdict(_whey(), Member(id="t", name="T", age=16), cfg)
    assert _codes(v) == [("supplement_child", Status.CAUTION)]
    assert v.status == Status.CAUTION


@pytest.mark.parametrize("age", [0, 1])
def test_supplement_infant_avoid(cfg, age):
    v = _verdict(_whey(), Member(id="i", name="I", age=age), cfg)
    assert ("supplement_infant", Status.AVOID) in _codes(v)
    assert ("supplement_child", Status.CAUTION) not in _codes(v)
    assert v.status == Status.AVOID


def test_adult_has_no_supplement_reason(cfg):
    assert _verdict(_whey(), Member(id="a", name="A", age=18), cfg).reasons == ()


def test_supplement_age_unknown_is_unknown(cfg):
    v = _verdict(_whey(), Member(id="n", name="N", age=None), cfg)
    assert ("age_unknown", Status.UNKNOWN) in _codes(v)
    assert not any(r.code.startswith("supplement_") for r in v.reasons)
    assert v.status == Status.UNKNOWN


def test_adult_supplement_not_ok_on_grade_alone(cfg):
    # No grade: the status comes from the other rules only. Plain adult: ok, no reasons.
    assert _verdict(_whey(), ADULT, cfg).status == Status.OK
    # A diabetic adult still gets the sugar and cardio rules.
    sugary = _whey(per_100g=replace(_whey().per_100g, sugars_g=30, carbs_g=40))
    v = _verdict(sugary, Member(id="d", name="D", age=40, conditions=("diabetes",)), cfg)
    assert ("sugar_high", Status.AVOID) in _codes(v)
    # Missing data still makes it unknown, never ok.
    blank = _whey(per_100g=Nutrients(protein_g=80), ingredients=())
    v = _verdict(blank, Member(id="m", name="M", age=30, allergens=("milk",)), cfg)
    assert v.status == Status.UNKNOWN


def test_weight_loss_member_no_nutriscore_low_for_supplement(cfg):
    m = Member(id="w", name="W", age=30, goal="weight_loss")
    v = _verdict(_whey(), m, cfg)
    assert not any(r.code == "nutriscore_low" for r in v.reasons)
    assert any(r.code == "good_protein_density" for r in v.reasons)


def test_protein_facts_still_reported(cfg):
    p = analyze(_whey(), [], cfg).report.protein
    assert (p.per_100g, p.per_serving, p.per_100kcal) == (80.0, 24.0, 20.0)


def test_claims_still_checked_on_supplement(cfg):
    p = _whey(
        claims=("30g protein per scoop", "100% whey", "sugar free"),
        ingredients=("whey protein concentrate", "soy protein isolate"),
    )
    claims = {c.claim: c for c in analyze(p, [], cfg).report.claims}
    assert claims["protein_amount"].verdict == ClaimVerdict.CONTRADICTED
    assert claims["whey_only"].reason_code == "other_protein_source"
    assert claims["sugar_free"].verdict == ClaimVerdict.CONTRADICTED


# --- detection ---------------------------------------------------------------------------


def _off(tags):
    return {
        "code": "8900000000999",
        "product_name": "Whey",
        "categories_tags": tags,
        "nutriments": {"energy-kcal_100g": 400, "proteins_100g": 80},
    }


@pytest.mark.parametrize("tag", SUPPLEMENT_TAGS)
def test_off_supplement_tags_map_to_supplement(tag):
    # Checked before every other category, including the drink and powder tags.
    tags = ["en:beverages", "en:beverage-preparations", "en:dairies", tag]
    assert off_to_product(_off(tags), confidence=0.9).category == Category.SUPPLEMENT


def test_off_supplement_tags_listed():
    assert SUPPLEMENT_TAGS == (
        "en:dietary-supplements",
        "en:protein-powders",
        "en:bodybuilding-supplements",
        "en:whey-proteins",
        "en:sports-nutrition-supplements",
    )


def test_off_without_supplement_tag_is_not_supplement():
    assert off_to_product(_off(["en:snacks"]), confidence=0.9).category == Category.GENERAL


def test_normalizer_never_proposes_supplement():
    guesses = get_args(NutritionExtraction.model_fields["category_guess"].annotation)
    assert "supplement" not in {a for g in guesses for a in (get_args(g) or (g,))}
    for unit in (None, "ml"):
        draft = to_draft(ex(category_guess=None, per_100_unit=unit))
        assert draft.category != "supplement"
    forced = to_draft(ex().model_copy(update={"category_guess": "supplement"}))
    assert forced.category == "general" and "category_unknown" in forced.warnings

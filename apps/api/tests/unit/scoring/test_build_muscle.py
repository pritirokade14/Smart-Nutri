"""Plan 9 Task 3: the `build_muscle` goal and the protein target by goal.

A goal is a preference (Ruling R34): `build_muscle` may add an OK-level
`good_protein_density` reason only, never a caution or an avoid, and the protein target
(1.6 g/kg, adults with a weight only) never changes a verdict.
"""

from dataclasses import replace

import pytest

from app.scoring import Member, Nutrients, Product, Status, analyze, daily_limits_for
from app.scoring.models import Category
from tests.fixtures.loader import FIXTURES, load_member, load_product


@pytest.fixture
def high_protein_product():
    # 25 g protein / 380 kcal = 6.6 g per 100 kcal (>= 5).
    return Product(
        name="Paneer Bites",
        category=Category.GENERAL,
        per_100g=Nutrients(
            energy_kcal=380,
            protein_g=25,
            carbs_g=30,
            sugars_g=3,
            fat_g=18,
            sat_fat_g=8,
            fiber_g=1,
            salt_g=1.0,
        ),
        serving_size_g=30,
        ingredients=("paneer", "rice flour", "salt"),
    )


@pytest.fixture(scope="module")
def all_fixture_products():
    return [load_product(p.stem) for p in sorted((FIXTURES / "products").glob("*.json"))]


def _fixture_members():
    return [load_member(m.stem) for m in sorted((FIXTURES / "members").glob("*.json"))]


# --- protein target ----------------------------------------------------------------------


def test_protein_target_by_goal(cfg):
    m = Member(id="g", name="G", age=25, goal="build_muscle")
    assert daily_limits_for(m, 70.0, cfg).protein_target_g == pytest.approx(112.0)


@pytest.mark.parametrize("age", [17, None])
def test_no_target_under_18_or_unknown_age(cfg, age):
    m = Member(id="g", name="G", age=age, goal="build_muscle")
    assert daily_limits_for(m, 70.0, cfg).protein_target_g is None


def test_no_target_without_weight(cfg):
    m = Member(id="g", name="G", age=30, goal="build_muscle")
    assert daily_limits_for(m, None, cfg).protein_target_g is None


def test_other_goals_keep_adult_value(cfg):
    m = Member(id="w", name="W", age=30, goal="weight_loss")
    assert daily_limits_for(m, 70.0, cfg).protein_target_g == pytest.approx(58.1)


@pytest.mark.parametrize("goal", [None, "healthy_eating", "weight_gain", "something_else"])
def test_unlisted_goals_keep_adult_value(cfg, goal):
    m = Member(id="w", name="W", age=30, goal=goal)
    assert daily_limits_for(m, 70.0, cfg).protein_target_g == pytest.approx(58.1)


def test_target_reads_yaml(cfg):
    assert cfg.thresholds["daily_limits"]["protein_g_per_kg_by_goal"] == {"build_muscle": 1.6}


def test_build_muscle_keeps_child_sugar_and_salt_limits(cfg):
    child = daily_limits_for(Member(id="c", name="C", age=8, goal="build_muscle"), 30.0, cfg)
    plain = daily_limits_for(Member(id="c", name="C", age=8), 30.0, cfg)
    assert child == plain


# --- the build_muscle condition group ----------------------------------------------------


def test_good_protein_density_is_ok_reason(cfg, high_protein_product):
    m = Member(id="g", name="G", age=25, goal="build_muscle")
    verdict = analyze(high_protein_product, [m], cfg).verdicts[0]
    assert verdict.status == Status.OK
    assert [(r.code, r.severity) for r in verdict.reasons] == [("good_protein_density", Status.OK)]
    assert verdict.reasons[0].params == {"protein_g_per_100kcal": 6.58}


@pytest.mark.parametrize("goal", ["build_muscle", "weight_loss"])
@pytest.mark.parametrize("age", [1, 10, 17, None])
def test_no_good_protein_density_for_minors_or_unknown_age(cfg, high_protein_product, goal, age):
    """P9 safety S4: protein praise is for adults only (daily_limits.protein_min_age)."""
    m = Member(id="g", name="G", age=age, goal=goal)
    verdict = analyze(high_protein_product, [m], cfg).verdicts[0]
    assert "good_protein_density" not in {r.code for r in verdict.reasons}


@pytest.mark.parametrize("goal", ["build_muscle", "weight_loss"])
def test_good_protein_density_from_protein_min_age(cfg, high_protein_product, goal):
    age = cfg.thresholds["daily_limits"]["protein_min_age"]
    assert age == 18
    m = Member(id="g", name="G", age=age, goal=goal)
    verdict = analyze(high_protein_product, [m], cfg).verdicts[0]
    assert "good_protein_density" in {r.code for r in verdict.reasons}


def test_weight_loss_minor_keeps_its_cautions(cfg, high_protein_product):
    """Only the OK-level praise is age-gated; weight_loss cautions still apply to a minor."""
    dense = replace(
        high_protein_product, per_100g=replace(high_protein_product.per_100g, energy_kcal=450)
    )
    m = Member(id="g", name="G", age=15, goal="weight_loss")
    codes = {r.code for r in analyze(dense, [m], cfg).verdicts[0].reasons}
    assert "energy_dense" in codes and "good_protein_density" not in codes


def test_low_protein_density_adds_nothing(cfg, high_protein_product):
    low = replace(
        high_protein_product, per_100g=replace(high_protein_product.per_100g, protein_g=4)
    )
    m = Member(id="g", name="G", age=25, goal="build_muscle")
    assert analyze(low, [m], cfg).verdicts[0].reasons == ()


def test_missing_protein_adds_no_unknown_for_build_muscle(cfg, high_protein_product):
    # A goal is a preference: a missing value is not a health risk, so no nutrient_missing.
    blank = replace(
        high_protein_product, per_100g=replace(high_protein_product.per_100g, protein_g=None)
    )
    m = Member(id="g", name="G", age=25, goal="build_muscle")
    verdict = analyze(blank, [m], cfg).verdicts[0]
    assert verdict.status == Status.OK and verdict.reasons == ()


def test_build_muscle_never_cautions_on_energy_or_grade(cfg, all_fixture_products):
    m = Member(id="g", name="G", age=25, goal="build_muscle")
    for product in all_fixture_products:
        codes = {r.code for r in analyze(product, [m], cfg).verdicts[0].reasons}
        assert not codes & {"energy_dense", "nutriscore_low", "nutrient_missing"}, product.name


def test_build_muscle_never_changes_status(cfg, all_fixture_products):
    for product in all_fixture_products:
        for member in _fixture_members():
            base = replace(member, goal=None)
            muscle = replace(member, goal="build_muscle")
            a = analyze(product, [base], cfg).verdicts[0]
            b = analyze(product, [muscle], cfg).verdicts[0]
            assert a.status == b.status, (product.name, member.id)
            extra = [(r.code, r.severity) for r in b.reasons if r not in a.reasons]
            missing = [r for r in a.reasons if r not in b.reasons]
            assert missing == [], (product.name, member.id)
            assert extra in ([], [("good_protein_density", Status.OK)]), (product.name, member.id)


# --- protein g/kg basis (P9 integration f3: the protein.guide copy) ------------------------


def test_protein_per_kg_by_goal(cfg):
    m = Member(id="g", name="G", age=25, goal="build_muscle")
    assert daily_limits_for(m, 70.0, cfg).protein_g_per_kg == pytest.approx(1.6)


@pytest.mark.parametrize("goal", [None, "weight_loss", "healthy_eating"])
def test_protein_per_kg_adult_default(cfg, goal):
    m = Member(id="w", name="W", age=30, goal=goal)
    assert daily_limits_for(m, 70.0, cfg).protein_g_per_kg == pytest.approx(0.83)


@pytest.mark.parametrize(("age", "weight"), [(17, 70.0), (None, 70.0), (30, None), (30, 0.0)])
def test_protein_per_kg_null_whenever_target_is_null(cfg, age, weight):
    m = Member(id="g", name="G", age=age, goal="build_muscle")
    limits = daily_limits_for(m, weight, cfg)
    assert limits.protein_target_g is None and limits.protein_g_per_kg is None

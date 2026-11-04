"""Plan 9 Task 4: protein facts, sweeteners and caffeine in the product report.

Information only (P9-R12): none of these change a verdict. Every number comes from the
SANITISED product and a missing input stays None, never 0 (Global Constraint 2).
"""

from dataclasses import replace

import pytest

from app.scoring import Nutrients, Product, ProteinFacts, analyze
from app.scoring.models import Category


def _whey(**kw):
    base = Product(
        name="Whey",
        category=Category.GENERAL,
        per_100g=Nutrients(energy_kcal=400, protein_g=25, carbs_g=40, sugars_g=5, fat_g=10),
        serving_size_g=30,
        ingredients=("whey protein concentrate", "cocoa", "sucralose", "caffeine"),
    )
    return replace(base, **kw)


def _report(product, cfg):
    return analyze(product, [], cfg).report


def test_per_serving_and_per_100kcal(cfg):
    assert _report(_whey(), cfg).protein == ProteinFacts(
        per_100g=25.0, per_serving=7.5, per_100kcal=6.3, serving_size_g=30.0
    )


def test_none_stays_none(cfg):
    no_kcal = _whey(per_100g=Nutrients(protein_g=25))
    assert _report(no_kcal, cfg).protein.per_100kcal is None
    assert _report(no_kcal, cfg).protein.per_serving == 7.5
    no_serving = _whey(serving_size_g=None)
    facts = _report(no_serving, cfg).protein
    assert facts.per_serving is None and facts.serving_size_g is None
    assert facts.per_100kcal == 6.3
    no_protein = _whey(per_100g=Nutrients(energy_kcal=400))
    assert _report(no_protein, cfg).protein == ProteinFacts(
        per_100g=None, per_serving=None, per_100kcal=None, serving_size_g=30.0
    )


def test_zero_kcal_is_none(cfg):
    facts = _report(_whey(per_100g=Nutrients(energy_kcal=0, protein_g=0)), cfg).protein
    assert facts.per_100kcal is None
    assert facts.per_100g == 0.0 and facts.per_serving == 0.0


def test_implausible_values_are_dropped_first(cfg):
    # 140 g protein per 100 g is impossible: sanitised to None, so no protein facts.
    facts = _report(_whey(per_100g=Nutrients(energy_kcal=400, protein_g=140)), cfg).protein
    assert facts.per_100g is None and facts.per_serving is None and facts.per_100kcal is None
    bad_serving = _report(_whey(serving_size_g=-5), cfg).protein
    assert bad_serving.per_serving is None and bad_serving.serving_size_g is None


@pytest.mark.parametrize(
    ("protein", "kcal", "expected"),
    [(25, 400, 6.3), (10, 300, 3.3), (1, 3, 33.3), (7.45, 100, 7.5)],
)
def test_per_100kcal_rounds_half_up_to_1dp(cfg, protein, kcal, expected):
    facts = _report(_whey(per_100g=Nutrients(energy_kcal=kcal, protein_g=protein)), cfg).protein
    assert facts.per_100kcal == expected


def test_sweeteners_and_caffeine_listed(cfg):
    report = _report(_whey(), cfg)
    assert report.sweeteners == ("sucralose",)
    assert report.caffeine == ("caffeine",)
    plain = _report(_whey(ingredients=("whey protein concentrate", "cocoa")), cfg)
    assert plain.sweeteners == () and plain.caffeine == ()


def test_off_sweetener_flag_listed(cfg):
    flagged = _whey(ingredients=("whey protein concentrate",), contains_sweeteners=True)
    assert _report(flagged, cfg).sweeteners == ("contains_sweeteners",)
    # A matched term wins: the flag is only added when no term matched.
    both = _whey(contains_sweeteners=True)
    assert _report(both, cfg).sweeteners == ("sucralose",)
    unknown = _whey(ingredients=(), contains_sweeteners=True)
    assert _report(unknown, cfg).sweeteners == ("contains_sweeteners",)


def test_report_serialises_protein_sweeteners_and_caffeine(cfg):
    data = analyze(_whey(), [], cfg).to_dict()["report"]
    assert data["protein"] == {
        "per_100g": 25.0,
        "per_serving": 7.5,
        "per_100kcal": 6.3,
        "serving_size_g": 30.0,
    }
    assert data["sweeteners"] == ["sucralose"]
    assert data["caffeine"] == ["caffeine"]

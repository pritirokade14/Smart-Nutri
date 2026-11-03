"""Plan 9 Task 4: protein and whey claim checks against the nutrition table and ingredients.

The new claim keys are matched before `high_protein` and `source_of_protein`, and they add
NO member reason (P9-R12): a verdict never changes because of them.
"""

from dataclasses import replace

import pytest

from app.scoring import Nutrients, Product, analyze
from app.scoring.claims import check_claims
from app.scoring.models import Category, ClaimVerdict
from tests.fixtures.loader import FIXTURES, load_member, load_product


def _whey(**kw):
    base = Product(
        name="Whey",
        category=Category.GENERAL,
        # 80 g protein per 100 g; a 30 g scoop -> 24 g.
        per_100g=Nutrients(energy_kcal=400, protein_g=80, carbs_g=8, sugars_g=4, fat_g=6),
        serving_size_g=30,
        ingredients=("whey protein concentrate", "whey protein isolate", "cocoa", "sucralose"),
    )
    return replace(base, **kw)


def _one(product, cfg):
    (c,) = check_claims(product, cfg)
    return c


# --- protein_amount ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "claim", ["24g protein per scoop", "24 g Protein per serving", "24g of protein / serve"]
)
def test_protein_amount_supported_per_scoop(cfg, claim):
    c = _one(_whey(claims=(claim,)), cfg)
    assert (c.claim, c.verdict, c.reason_code) == (
        "protein_amount",
        ClaimVerdict.SUPPORTED,
        "ok",
    )


def test_protein_amount_within_tolerance_supported(cfg):
    # 24 g per scoop on the table vs 26 g claimed: 7.7 % short, inside the 10 % tolerance.
    c = _one(_whey(claims=("26g protein per scoop",)), cfg)
    assert c.verdict == ClaimVerdict.SUPPORTED


def test_protein_amount_below_claimed(cfg):
    c = _one(_whey(claims=("30g protein per scoop",)), cfg)
    assert (c.claim, c.verdict, c.reason_code) == (
        "protein_amount",
        ClaimVerdict.CONTRADICTED,
        "below_claimed",
    )
    assert c.params == {"value": 24.0, "claimed": 30.0, "basis": "per_serving"}


@pytest.mark.parametrize(
    "claim", ["90 g protein per 100 g", "90g protein/100g", "Protein: 90 g per 100g"]
)
def test_protein_amount_per_100g_when_stated(cfg, claim):
    short = _one(_whey(claims=(claim,)), cfg)
    assert short.verdict == ClaimVerdict.CONTRADICTED
    assert short.params == {"value": 80.0, "claimed": 90.0, "basis": "per_100g"}
    assert _one(_whey(claims=("80g protein per 100 g",)), cfg).verdict == ClaimVerdict.SUPPORTED


def test_protein_amount_without_basis_never_contradicted(cfg):
    """P9 safety S2: a claim that names no basis may mean per pack, per bar or per serving:
    supported when either the per-100 g or the per-serving value meets it, else
    unverifiable (`basis_unknown`), never contradicted."""
    assert _one(_whey(claims=("80g protein",)), cfg).verdict == ClaimVerdict.SUPPORTED
    short = _one(_whey(claims=("90 g protein",)), cfg)
    assert (short.verdict, short.reason_code, short.params) == (
        ClaimVerdict.UNVERIFIABLE,
        "basis_unknown",
        {},
    )


def test_thirty_g_per_bar_on_a_200_g_bar_is_not_contradicted(cfg):
    """The reviewer's probe: 15 g protein per 100 g, a 200 g bar, "30g protein per bar"."""
    p = _whey(
        per_100g=Nutrients(energy_kcal=400, protein_g=15), serving_size_g=200,
        claims=("30g protein per bar",),
    )  # fmt: skip
    c = _one(p, cfg)
    assert c.claim == "protein_amount"
    assert c.verdict in (ClaimVerdict.SUPPORTED, ClaimVerdict.UNVERIFIABLE)
    assert c.verdict == ClaimVerdict.SUPPORTED


@pytest.mark.parametrize("unit", ["bar", "pack", "sachet", "bottle", "piece", "cup", "bars"])
def test_package_units_are_per_serving(cfg, unit):
    # 80 g per 100 g, 30 g serving -> 24 g per serving.
    ok = _one(_whey(claims=(f"24g protein per {unit}",)), cfg)
    assert ok.verdict == ClaimVerdict.SUPPORTED


@pytest.mark.parametrize("unit", ["bar", "pack", "sachet", "bottle", "piece", "cup"])
def test_package_unit_short_of_the_serving_is_unverifiable(cfg, unit):
    """The serving may be part of a bar or pack, so a shortfall is never a contradiction."""
    c = _one(_whey(claims=(f"40g protein per {unit}",)), cfg)
    assert (c.verdict, c.reason_code) == (ClaimVerdict.UNVERIFIABLE, "basis_unknown")


def test_package_unit_without_serving_size_unverifiable(cfg):
    c = _one(_whey(serving_size_g=None, claims=("24g protein per bar",)), cfg)
    assert (c.verdict, c.reason_code, c.params) == (
        ClaimVerdict.UNVERIFIABLE,
        "nutrient_missing",
        {"nutrient": "serving_size_g"},
    )


def test_protein_amount_decimal_claim(cfg):
    c = _one(_whey(claims=("24.5g protein per scoop",)), cfg)
    assert c.verdict == ClaimVerdict.SUPPORTED


def test_protein_amount_without_serving_unverifiable(cfg):
    c = _one(_whey(serving_size_g=None, claims=("24g protein per scoop",)), cfg)
    assert (c.claim, c.verdict, c.reason_code) == (
        "protein_amount",
        ClaimVerdict.UNVERIFIABLE,
        "nutrient_missing",
    )
    assert c.params == {"nutrient": "serving_size_g"}


def test_protein_amount_without_protein_unverifiable(cfg):
    p = _whey(per_100g=Nutrients(energy_kcal=400), claims=("24g protein per scoop",))
    c = _one(p, cfg)
    assert (c.verdict, c.reason_code, c.params) == (
        ClaimVerdict.UNVERIFIABLE,
        "nutrient_missing",
        {"nutrient": "protein_g"},
    )


# --- whey_only / whey_protein ------------------------------------------------------------


@pytest.mark.parametrize("claim", ["100% Whey", "Pure Whey Protein", "100 % whey protein"])
def test_whey_only_supported(cfg, claim):
    c = _one(_whey(claims=(claim,)), cfg)
    assert (c.claim, c.verdict, c.reason_code) == ("whey_only", ClaimVerdict.SUPPORTED, "ok")


def test_whey_only_with_soy_protein_contradicted(cfg):
    p = _whey(
        claims=("100% whey",),
        ingredients=("whey protein concentrate", "soy protein isolate", "cocoa"),
    )
    c = _one(p, cfg)
    assert (c.claim, c.verdict, c.reason_code) == (
        "whey_only",
        ClaimVerdict.CONTRADICTED,
        "other_protein_source",
    )
    assert c.params == {"ingredients": ["soy protein isolate"]}


@pytest.mark.parametrize(
    "other",
    [
        "skimmed milk powder",
        "skim milk powder",
        "milk solids",
        "milk protein isolate",
        "milk protein concentrate",
        "egg albumin",
        "egg white powder",
    ],
)
def test_whey_only_with_milk_or_egg_protein_contradicted(cfg, other):
    """P9 safety S1: milk powders, milk solids, milk proteins and egg proteins are other
    protein sources, so "100% whey" is contradicted."""
    p = _whey(claims=("100% whey",), ingredients=("whey protein concentrate", other, "cocoa"))
    c = _one(p, cfg)
    assert (c.verdict, c.reason_code) == (ClaimVerdict.CONTRADICTED, "other_protein_source")
    assert c.params["ingredients"]


def test_soy_lecithin_is_not_another_protein_source(cfg):
    """Plain "soy" is deliberately not a protein term: soy lecithin is an emulsifier."""
    p = _whey(claims=("100% whey",), ingredients=("whey protein concentrate", "soy lecithin"))
    c = _one(p, cfg)
    assert (c.verdict, c.reason_code) == (ClaimVerdict.SUPPORTED, "ok")


def test_whey_only_without_whey_contradicted(cfg):
    c = _one(_whey(claims=("100% whey",), ingredients=("maltodextrin", "cocoa")), cfg)
    assert (c.verdict, c.reason_code) == (ClaimVerdict.CONTRADICTED, "whey_not_listed")


def test_whey_not_listed(cfg):
    p = _whey(claims=("Whey Protein",), ingredients=("soy protein isolate", "cocoa"))
    c = _one(p, cfg)
    assert (c.claim, c.verdict, c.reason_code) == (
        "whey_protein",
        ClaimVerdict.CONTRADICTED,
        "whey_not_listed",
    )
    assert c.params == {}


def test_whey_protein_supported_with_hindi_term(cfg):
    c = _one(_whey(claims=("whey",), ingredients=("व्हे प्रोटीन", "कोको")), cfg)
    assert (c.claim, c.verdict) == ("whey_protein", ClaimVerdict.SUPPORTED)


@pytest.mark.parametrize(
    "claim",
    ["whey free", "Whey-Free", "No whey", "free from whey", "Free of whey", "without whey",
     "0% whey", "contains no whey", "whey protein free"],
)  # fmt: skip
def test_negated_whey_is_not_a_whey_claim(cfg, claim):
    """P9 safety S3: "whey free" is not a whey claim, so a pea-protein pack is never told
    that whey is missing."""
    p = _whey(claims=(claim,), ingredients=("pea protein", "cocoa"))
    assert check_claims(p, cfg) == ()


def test_negated_whey_still_checks_the_protein_part(cfg):
    p = _whey(claims=("Whey-free high protein",), ingredients=("pea protein", "cocoa"))
    assert _one(p, cfg).claim == "high_protein"


@pytest.mark.parametrize("claim", ["100% whey", "whey protein"])
def test_whey_ingredients_unknown_unverifiable(cfg, claim):
    c = _one(_whey(claims=(claim,), ingredients=()), cfg)
    assert (c.verdict, c.reason_code) == (ClaimVerdict.UNVERIFIABLE, "ingredients_unknown")


def test_whey_low_confidence_unverifiable(cfg):
    p = _whey(claims=("whey protein",), extraction_confidence=0.5)
    c = _one(p, cfg)
    assert (c.verdict, c.reason_code) == (ClaimVerdict.UNVERIFIABLE, "ingredients_unknown")


# --- existing protein claims still work --------------------------------------------------


def test_plain_protein_word_still_source_of_protein(cfg):
    assert _one(_whey(claims=("Protein",)), cfg).claim == "source_of_protein"
    assert _one(_whey(claims=("Protein Bar",)), cfg).claim == "source_of_protein"
    assert _one(_whey(claims=("High Protein",)), cfg).claim == "high_protein"


def test_wheat_is_not_whey(cfg):
    assert _one(_whey(claims=("wheat protein",)), cfg).claim == "source_of_protein"


# --- never changes a verdict -------------------------------------------------------------

_NEW_CLAIMS = ("24g protein per scoop", "100% whey", "whey protein", "30 g protein")


def test_new_claims_never_change_status(cfg):
    products = [load_product(p.stem) for p in sorted((FIXTURES / "products").glob("*.json"))]
    members = [load_member(m.stem) for m in sorted((FIXTURES / "members").glob("*.json"))]
    for product in products:
        with_claims = replace(product, claims=(*product.claims, *_NEW_CLAIMS))
        base = analyze(product, members, cfg)
        new = analyze(with_claims, members, cfg)
        assert {c.claim for c in new.report.claims} >= {"protein_amount", "whey_only"}
        for a, b in zip(base.verdicts, new.verdicts, strict=True):
            assert (a.status, a.reasons) == (b.status, b.reasons), (product.name, a.member_id)

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


def test_protein_amount_per_100g_when_no_serving_word(cfg):
    ok = _one(_whey(claims=("80g protein",)), cfg)
    assert ok.verdict == ClaimVerdict.SUPPORTED
    short = _one(_whey(claims=("90 g protein",)), cfg)
    assert short.verdict == ClaimVerdict.CONTRADICTED
    assert short.params == {"value": 80.0, "claimed": 90.0, "basis": "per_100g"}


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


def test_whey_only_without_whey_contradicted(cfg):
    c = _one(_whey(claims=("100% whey",), ingredients=("skimmed milk powder", "cocoa")), cfg)
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

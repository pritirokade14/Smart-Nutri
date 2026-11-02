from dataclasses import replace

from app.scoring.claims import check_claims
from app.scoring.models import ClaimVerdict


def test_sugar_free_biscuit_contradicted(sf_biscuit, cfg):
    (c,) = check_claims(sf_biscuit, cfg)
    assert (c.claim, c.verdict, c.reason_code) == ("sugar_free", ClaimVerdict.CONTRADICTED, "exceeds_limit")


def test_no_added_sugar_with_maltodextrin(sf_biscuit, cfg):
    (c,) = check_claims(replace(sf_biscuit, claims=("No Added Sugars*",)), cfg)
    assert c.verdict == ClaimVerdict.CONTRADICTED and c.params["ingredients"] == ["maltodextrin"]


def test_oats_high_protein_contradicted(oats, cfg):  # 13*4/389 = 13.4% -> not high (20%)
    (c,) = check_claims(oats, cfg)
    assert (c.claim, c.verdict) == ("high_protein", ClaimVerdict.CONTRADICTED)


def test_shouting_claim_recognised(curd, cfg):
    (c,) = check_claims(replace(curd, claims=("SUGAR-FREE!",)), cfg)
    assert c.claim == "sugar_free"


def test_unrecognised_claim_skipped(curd, cfg):
    assert check_claims(replace(curd, claims=("Tasty!",)), cfg) == ()


def test_missing_nutrient_unverifiable(no_ingredients, cfg):
    p = replace(no_ingredients, claims=("low fat",), per_100g=replace(no_ingredients.per_100g, fat_g=None))
    assert check_claims(p, cfg)[0].verdict == ClaimVerdict.UNVERIFIABLE


def test_no_added_sugar_unknown_ingredients(no_ingredients, cfg):
    (c,) = check_claims(replace(no_ingredients, claims=("no added sugar",)), cfg)
    assert (c.verdict, c.reason_code) == (ClaimVerdict.UNVERIFIABLE, "ingredients_unknown")


def test_protein_vs_high_protein_order(oats, cfg):
    r = check_claims(replace(oats, claims=("Source of Protein", "protein", "Protein Rich")), cfg)
    assert [c.claim for c in r] == ["source_of_protein", "source_of_protein", "high_protein"]
    assert r[0].verdict == ClaimVerdict.SUPPORTED and r[0].reason_code == "ok"


def test_params_json_friendly(oats, cfg):
    (c,) = check_claims(oats, cfg)
    assert c.reason_code == "below_minimum" and c.params == {"value": 13.37, "limit": 20}

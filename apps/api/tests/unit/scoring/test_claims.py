from dataclasses import replace

import pytest

from app.scoring.claims import check_claims
from app.scoring.models import Category, ClaimVerdict, Nutrients


def test_sugar_free_biscuit_contradicted(sf_biscuit, cfg):
    (c,) = check_claims(sf_biscuit, cfg)
    assert (c.claim, c.verdict, c.reason_code) == (
        "sugar_free",
        ClaimVerdict.CONTRADICTED,
        "exceeds_limit",
    )


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
    p = replace(
        no_ingredients, claims=("low fat",), per_100g=replace(no_ingredients.per_100g, fat_g=None)
    )
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
    assert c.reason_code == "below_minimum" and c.params == {"value": 13.368, "limit": 20}


def _with(product, claims, **nutrients):
    return replace(product, claims=claims, per_100g=replace(product.per_100g, **nutrients))


def test_no_sugar_added_with_maltodextrin_is_no_added_sugar(sf_biscuit, cfg):
    p = _with(sf_biscuit, ("No sugar added",), sugars_g=0.3)
    (c,) = check_claims(p, cfg)
    assert (c.claim, c.verdict) == ("no_added_sugar", ClaimVerdict.CONTRADICTED)
    assert c.params["ingredients"] == ["maltodextrin"]


def test_juice_no_sugar_added_supported(cfg, curd):
    juice = replace(
        _with(curd, ("No Sugar Added",), sugars_g=10.0),
        category=Category.BEVERAGE,
        ingredients=("apple juice",),
    )
    (c,) = check_claims(juice, cfg)
    assert (c.claim, c.verdict, c.reason_code) == ("no_added_sugar", ClaimVerdict.SUPPORTED, "ok")


def test_no_added_sugar_variants(curd, cfg):
    for text in ("Zero Added Sugar", "Without Added Sugar", "No Added Sugars"):
        (c,) = check_claims(replace(curd, claims=(text,)), cfg)
        assert c.claim == "no_added_sugar", text


def test_high_in_protein_variants(curd, cfg):
    p = _with(curd, ("High in Protein",), energy_kcal=400, protein_g=15)  # 15%
    (c,) = check_claims(p, cfg)
    assert (c.claim, c.verdict) == ("high_protein", ClaimVerdict.CONTRADICTED)
    (c,) = check_claims(replace(p, claims=("Rich in Protein",)), cfg)
    assert c.claim == "high_protein"


def test_drink_limit_low_sugar(cola, cfg):
    (c,) = check_claims(_with(cola, ("Low Sugar",), sugars_g=3.0), cfg)
    assert (c.verdict, c.reason_code) == (ClaimVerdict.CONTRADICTED, "exceeds_limit")
    assert c.params == {"value": 3.0, "limit": 2.5}
    (c,) = check_claims(_with(cola, ("Low Sugar",), sugars_g=2.5), cfg)
    assert c.verdict == ClaimVerdict.SUPPORTED


def test_salt_fallback_times_400(curd, cfg):
    base = _with(curd, ("Low Salt",), salt_g=0.3, sodium_mg=None)
    assert check_claims(base, cfg)[0].verdict == ClaimVerdict.SUPPORTED
    over = _with(curd, ("Low Salt",), salt_g=0.31, sodium_mg=None)
    assert check_claims(over, cfg)[0].verdict == ClaimVerdict.CONTRADICTED


def test_boundaries_inclusive(curd, cfg):
    (c,) = check_claims(_with(curd, ("Sugar Free",), sugars_g=0.5), cfg)
    assert c.verdict == ClaimVerdict.SUPPORTED
    (c,) = check_claims(_with(curd, ("High Protein",), energy_kcal=400, protein_g=20), cfg)
    assert c.verdict == ClaimVerdict.SUPPORTED


def test_breach_never_displays_equal_to_limit(curd, cfg):
    (c,) = check_claims(_with(curd, ("Sugar Free",), sugars_g=0.504), cfg)
    assert c.params == {"value": 0.504, "limit": 0.5}


# --- C11 (Ruling R28): claim phrasing gaps ---


@pytest.mark.parametrize("text", ["Sugarfree", "SUGARLESS", "0% Sugar", "0g sugar", "0 g Sugar"])
def test_sugar_free_variants(curd, cfg, text):
    (c,) = check_claims(_with(curd, (text,), sugars_g=4.0), cfg)
    assert (c.claim, c.verdict) == ("sugar_free", ClaimVerdict.CONTRADICTED), text


@pytest.mark.parametrize(
    "text", ["Added Sugar Free", "0% Added Sugar", "No added sugar or sweeteners"]
)
def test_no_added_sugar_more_variants(sf_biscuit, cfg, text):
    (c,) = check_claims(replace(sf_biscuit, claims=(text,)), cfg)
    assert (c.claim, c.verdict) == ("no_added_sugar", ClaimVerdict.CONTRADICTED), text


@pytest.mark.parametrize(
    "ingredient", ["sugar", "cane sugar", "refined sugar", "sucrose", "brown sugar", "icing sugar"]
)
def test_no_refined_sugar_contradicted(curd, cfg, ingredient):
    for text in ("No Refined Sugar", "no refined sugar added"):
        p = replace(curd, claims=(text,), ingredients=("oats", ingredient))
        (c,) = check_claims(p, cfg)
        assert (c.claim, c.verdict, c.reason_code) == (
            "no_refined_sugar",
            ClaimVerdict.CONTRADICTED,
            "refined_sugar_ingredient",
        )
        assert c.params == {"ingredients": [ingredient]}


def test_no_refined_sugar_supported_or_unverifiable(curd, no_ingredients, cfg):
    p = replace(curd, claims=("No Refined Sugar",), ingredients=("oats", "jaggery"))
    (c,) = check_claims(p, cfg)
    assert (c.claim, c.verdict, c.reason_code) == ("no_refined_sugar", ClaimVerdict.SUPPORTED, "ok")
    (c,) = check_claims(replace(no_ingredients, claims=("No Refined Sugar",)), cfg)
    assert (c.verdict, c.reason_code) == (ClaimVerdict.UNVERIFIABLE, "ingredients_unknown")


@pytest.mark.parametrize(
    "text",
    ["Diabetic Friendly", "diabetes-friendly", "Suitable for Diabetics", "Low GI", "low glycemic"],
)
def test_diabetic_friendly_always_unverifiable(oats, cfg, text):
    (c,) = check_claims(replace(oats, claims=(text,)), cfg)
    assert (c.claim, c.verdict, c.reason_code) == (
        "diabetic_friendly",
        ClaimVerdict.UNVERIFIABLE,
        "no_standard",
    )


def test_nutrient_missing_names_the_nutrient(no_ingredients, cfg):
    p = replace(
        no_ingredients,
        claims=("Sugar Free", "Low Fat", "Low Sodium", "High Protein"),
        per_100g=replace(
            no_ingredients.per_100g, sugars_g=None, fat_g=None, salt_g=None, protein_g=None
        ),
    )
    got = [(c.claim, c.reason_code, dict(c.params)) for c in check_claims(p, cfg)]
    assert got == [
        ("sugar_free", "nutrient_missing", {"nutrient": "sugars_g"}),
        ("low_fat", "nutrient_missing", {"nutrient": "fat_g"}),
        ("low_sodium", "nutrient_missing", {"nutrient": "sodium_mg"}),
        ("high_protein", "nutrient_missing", {"nutrient": "protein_g"}),
    ]
    q = replace(p, claims=("High Protein",), per_100g=Nutrients(protein_g=10))
    assert check_claims(q, cfg)[0].params == {"nutrient": "energy_kcal"}


def test_low_sodium_uses_higher_of_salt_and_sodium(curd, cfg):  # consistent with Ruling R22
    p = _with(curd, ("Low Sodium",), sodium_mg=10, salt_g=2.0)
    (c,) = check_claims(p, cfg)
    assert c.verdict == ClaimVerdict.CONTRADICTED and c.params["value"] == 800

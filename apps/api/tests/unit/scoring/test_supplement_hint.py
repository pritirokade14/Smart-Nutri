"""P9 safety S5: a deterministic "looks like a supplement" hint (never an LLM, never a verdict).

`supplement_suspect` is true for a product that is not already a supplement when its
ingredients name a whey or protein isolate/concentrate, or it has at least
`supplements.suspect_min_protein_g` protein per 100 g. It only drives a confirm-screen hint
and the protein-sort exclusion for members under 18; it never sets the category or changes
a verdict.
"""

import pytest

from app.scoring import Category, Member, Nutrients, Product, analyze
from app.scoring.supplements import hides_supplement_suspects, supplement_suspect


def _p(ingredients=(), protein=None, category=Category.GENERAL):
    return Product(
        name="x",
        category=category,
        per_100g=Nutrients(energy_kcal=400, protein_g=protein),
        ingredients=tuple(ingredients),
    )


@pytest.mark.parametrize(
    "ingredients",
    [
        ("whey protein concentrate", "cocoa"),
        ("Whey Protein Isolate (milk)",),
        ("hydrolysed whey", "sucralose"),
        ("soy protein isolate", "cocoa"),
        ("pea protein isolate",),
        ("milk protein concentrate", "sugar"),
        ("rice protein concentrate",),
        ("WPC 80", "cocoa"),
        ("व्हे प्रोटीन", "कोको"),
    ],
)
def test_protein_isolate_or_concentrate_ingredients_are_suspect(cfg, ingredients):
    assert supplement_suspect(_p(ingredients), cfg)


@pytest.mark.parametrize(
    "ingredients",
    [
        ("wheat flour", "sugar", "milk solids", "whey powder"),  # a biscuit
        ("sugar", "cocoa butter", "whey", "milk solids"),  # a chocolate
        ("soy lecithin", "wheat flour"),
        ("roasted chana", "salt"),
    ],
)
def test_ordinary_foods_with_whey_powder_are_not_suspect(cfg, ingredients):
    assert not supplement_suspect(_p(ingredients, protein=8), cfg)


def test_protein_threshold_from_data(cfg):
    limit = cfg.thresholds["supplements"]["suspect_min_protein_g"]
    assert limit == 50
    assert supplement_suspect(_p(protein=limit), cfg)
    assert not supplement_suspect(_p(protein=limit - 0.1), cfg)
    assert not supplement_suspect(_p(protein=None), cfg)


def test_a_supplement_is_never_suspect(cfg):
    p = _p(("whey protein concentrate",), protein=80, category=Category.SUPPLEMENT)
    assert not supplement_suspect(p, cfg)


@pytest.mark.parametrize(("age", "hides"), [(0, True), (9, True), (17, True), (None, True),
                                            (18, False), (45, False)])  # fmt: skip
def test_suspects_hidden_from_protein_sort_under_18_or_unknown_age(cfg, age, hides):
    assert hides_supplement_suspects(Member(id="m", name="", age=age), cfg) is hides


def test_the_hint_never_changes_a_verdict(cfg):
    """It is not read by analyze(): the same product gets the same verdicts either way."""
    p = _p(("whey protein concentrate", "cocoa"), protein=80)
    members = [Member(id="c", name="", age=9), Member(id="a", name="", age=30)]
    result = analyze(p, members, cfg)
    assert result.report.nutriscore.reason != "not_scored_supplement"
    assert [r.code for v in result.verdicts for r in v.reasons].count("supplement_child") == 0


# --- P9 integration q3: legumes, soya chunks and dairy are not flagged by protein alone -------


@pytest.mark.parametrize(
    ("ingredients", "protein", "category"),
    [
        (("defatted soya flour",), 52, Category.GENERAL),  # soya chunks
        (("soya chunks",), 52, Category.GENERAL),
        (("Soya Nuggets (Defatted Soy Flour)",), 54, Category.GENERAL),
        (("सोया चंक्स",), 52, Category.GENERAL),
        (("milk", "citric acid"), 55, Category.GENERAL),  # high-protein paneer
        (("paneer",), 55, Category.GENERAL),
        (("पनीर",), 55, Category.GENERAL),
        ((), 55, Category.CHEESE),  # a dairy category, ingredients unknown
        (("skimmed milk", "live cultures"), 50, Category.GENERAL),  # skyr
        (("skyr",), 50, Category.GENERAL),
        (("roasted chana", "salt"), 50, Category.GENERAL),  # a legume
        (("moong dal",), 50, Category.GENERAL),
    ],
)
def test_legumes_soya_and_dairy_are_not_suspect_by_protein_alone(
    cfg, ingredients, protein, category
):
    assert not supplement_suspect(_p(ingredients, protein=protein, category=category), cfg)


@pytest.mark.parametrize(
    ("ingredients", "category"),
    [
        (("defatted soya flour", "whey protein isolate"), Category.GENERAL),
        (("milk", "whey protein concentrate"), Category.GENERAL),
        (("skimmed milk", "milk protein concentrate"), Category.GENERAL),
        (("whey protein isolate",), Category.CHEESE),
    ],
)
def test_whey_isolate_or_concentrate_still_flags_them(cfg, ingredients, category):
    assert supplement_suspect(_p(ingredients, protein=60, category=category), cfg)


@pytest.mark.parametrize(
    "ingredients",
    [
        ("pea protein", "cocoa"),  # a protein powder, first ingredient a protein
        ("roasted chana", "soy protein", "cocoa"),  # a named protein anywhere
        ("wheat gluten", "salt"),  # not a legume, soya or dairy food
        ("cocoa", "milk"),  # the dairy food is not the main ingredient
    ],
)
def test_other_high_protein_products_are_still_suspect(cfg, ingredients):
    assert supplement_suspect(_p(ingredients, protein=60), cfg)


def test_whole_food_terms_live_in_data(cfg):
    s = cfg.thresholds["supplements"]
    assert {"soya chunks", "defatted soya flour", "paneer", "skyr", "milk"} <= set(
        s["suspect_whole_food_terms"]
    )
    assert s["suspect_whole_food_categories"] == ["cheese"]


# --- P9 final review: caseins are protein-powder words -------------------------------------


@pytest.mark.parametrize(
    "ingredients",
    [
        ("milk solids", "calcium caseinate"),  # first ingredient is a dairy food
        ("milk", "sodium caseinate", "cocoa"),
        ("skimmed milk", "casein"),
        ("milk solids", "milk protein"),
    ],
)
def test_casein_and_milk_protein_flag_a_dairy_first_powder(cfg, ingredients):
    p = _p(ingredients, protein=65)
    assert supplement_suspect(p, cfg)
    # ... so a protein-sorted list for a minor leaves it out.
    assert hides_supplement_suspects(Member(id="m", name="", age=12), cfg)


def test_casein_words_live_in_data(cfg):
    words = set(cfg.thresholds["supplements"]["suspect_protein_words"])
    assert {"casein", "caseinate", "calcium caseinate", "milk protein"} <= words

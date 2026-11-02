from dataclasses import replace

import pytest

from app.scoring.warnings import (
    added_sugar_terms,
    hidden_sugars,
    high_in,
    ingredient_hits,
    sodium_additives,
)


def test_high_in_biscuit(sf_biscuit, cfg):
    assert high_in(sf_biscuit, cfg) == ("sat_fat",)


def test_high_in_namkeen(namkeen, cfg):
    assert high_in(namkeen, cfg) == ("fat", "sat_fat", "salt")


def test_drink_threshold(cola, cfg):
    assert high_in(cola, cfg) == ()  # 10.6 < 11.25


def test_drink_high_sugar(cola, cfg):
    assert high_in(replace(cola, per_100g=replace(cola.per_100g, sugars_g=12)), cfg) == ("sugar",)


def test_missing_values_never_warn(no_ingredients, cfg):
    p = replace(no_ingredients, per_100g=replace(no_ingredients.per_100g, sugars_g=None, salt_g=None))
    assert "sugar" not in high_in(p, cfg)
    assert "salt" not in high_in(p, cfg)


def test_hidden_sugars(sf_biscuit, cfg):
    assert hidden_sugars(sf_biscuit, cfg) == ("maltodextrin",)


def test_added_sugar_terms(cola, cfg):
    assert added_sugar_terms(cola, cfg) == ("sugar",)


def test_sodium_additives(sf_biscuit, cfg):
    assert sodium_additives(sf_biscuit, cfg) == ("ins500",)


# --- final safety review: term-list regressions -------------------------------------------
def _with(base, *ings):
    return replace(base, ingredients=tuple(ings))


@pytest.mark.parametrize("term", ["tea", "chai", "चाय", "green tea extract", "matcha", "mate", "kola nut", "कॉफी"])
def test_caffeine_new_terms(term, no_ingredients, cfg):
    assert ingredient_hits(_with(no_ingredients, "water", term), cfg, "caffeine")


@pytest.mark.parametrize("text", ["steam", "tear gas", "tomato", "chocolate"])
def test_caffeine_no_overmatch(text, no_ingredients, cfg):
    assert not ingredient_hits(_with(no_ingredients, text), cfg, "caffeine")


@pytest.mark.parametrize(
    "term", ["शहद", "साखर", "apple juice concentrate", "गूळ", "coconut sugar", "agave", "fruit juice"]
)
def test_added_sugar_new_terms(term, no_ingredients, cfg):
    assert added_sugar_terms(_with(no_ingredients, "water", term), cfg)


@pytest.mark.parametrize("term", ["sodium chloride", "मीठ", "namak", "lavan", "सैंधव"])
def test_salt_new_terms(term, no_ingredients, cfg):
    assert ingredient_hits(_with(no_ingredients, "flour", term), cfg, "salt")

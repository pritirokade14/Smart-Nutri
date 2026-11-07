"""The recipe golden files (Plan 12 Task 12; spec 9.3): the API's stored and displayed values
equal the expectations generated from the same arithmetic, and a recipe is hand-checked once."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.generate_recipe_expectations import ROOT, expected_for
from tests.api.recipes.conftest import bar

URL = "/v1/recipes"
INPUTS = sorted((ROOT / "inputs").glob("*.json"))


def test_fixture_files_pair_up():
    assert len(INPUTS) == 8
    assert {p.name for p in INPUTS} == {p.name for p in (ROOT / "expected").glob("*.json")}


@pytest.mark.parametrize("path", INPUTS, ids=lambda p: p.stem)
def test_matches_fixtures(path: Path):
    case = json.loads(path.read_text())
    want = json.loads((ROOT / "expected" / path.name).read_text())
    assert json.loads(json.dumps(expected_for(case), sort_keys=True)) == want


def test_recipe_missing_fibre_by_hand():
    case = json.loads((ROOT / "inputs" / "recipe_missing_fibre.json").read_text())
    want = json.loads((ROOT / "expected" / "recipe_missing_fibre.json").read_text())
    ing = case["ingredients"]
    g1, g2, g3 = (Decimal(str(i["amount"])) for i in ing)
    f1, f2 = (Decimal(str(i["per_100"]["fibre_g"])) for i in ing[:2])
    assert ing[2]["per_100"]["fibre_g"] is None
    basis = g1 + g2 + g3
    fibre = (f1 * g1 / 100 + f2 * g2 / 100) / basis * 100  # ingredient 3 left out: a lower bound
    assert want["per_100g"]["fibre_g"] == float(fibre.quantize(Decimal("0.1")))
    assert want["incomplete_nutrients"] == ["fibre_g"]
    assert want["entry_snapshot_per_100"]["fibre_g"] is None  # a diary entry never counts it
    assert want["entry_snapshot_per_100"]["protein_g"] is not None


def test_all_unknown_is_null_never_zero():
    want = json.loads((ROOT / "expected" / "recipe_all_unknown_sat_fat.json").read_text())
    assert (
        want["per_100g"]["sat_fat_g"] is None
        and want["entry_snapshot_per_100"]["sat_fat_g"] is None
    )
    assert "sat_fat_g" in want["incomplete_nutrients"]


@pytest.mark.parametrize("path", INPUTS, ids=lambda p: p.stem)
async def test_api_matches_fixtures(path: Path, client, consented):
    """Every input case through the real routes: ingredients become custom foods with exactly
    the input's per-100 values (a null stays unknown), the recipe response equals the golden."""
    want = json.loads((ROOT / "expected" / path.name).read_text())
    case = json.loads(path.read_text())
    ingredients = []
    for n, i in enumerate(case["ingredients"]):
        nutrients = {k: v for k, v in i["per_100"].items() if v is not None}
        body = bar(
            name=f"{i['name']} {n}",
            basis=i["basis"],
            nutrients=nutrients,
            density_g_per_ml=i.get("density_g_per_ml"),
        )
        r = await client.post("/v1/custom-foods", json=body)
        assert r.status_code == 201, r.text
        ingredients.append(
            {"custom_food_id": r.json()["id"], "quantity": i["amount"], "unit": i["basis"]}
        )
    r = await client.post(
        URL,
        json={
            "name": case["name"],
            "servings": case["servings"],
            "cooked_weight_g": case["cooked_weight_g"],
            "ingredients": ingredients,
        },
    )
    if "error" in want:
        assert r.status_code == 422, r.text
        err = r.json()["error"]
        assert (err["code"], err["details"]) == (want["error"]["code"], want["error"]["details"])
        return
    assert r.status_code == 201, r.text
    got = r.json()
    assert got["total_raw_g"] == want["total_raw_g"]
    assert got["basis_weight_g"] == want["basis_weight_g"]
    assert got["incomplete_nutrients"] == want["incomplete_nutrients"]
    assert got["per_100g"] == want["per_100g"]
    assert got["per_serving"] == want["per_serving"]

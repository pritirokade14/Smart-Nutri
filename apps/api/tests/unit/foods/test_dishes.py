"""The 30 documented dishes (Plan 12 Task 3; G7, G8)."""

import json
import re
import shutil
from decimal import Decimal
from pathlib import Path

import yaml

from app.features.foods import recipe_math
from app.features.foods.seed import (
    DATA_DIR,
    dish_per_100,
    fdc_nutrients,
    food_rows,
    load_seed_data,
    report_for,
)

REPO = Path(__file__).resolve().parents[5]
DOC = REPO / "docs/research/food-diary/data/indian_dishes_recipes.md"
FIXTURE = REPO / "packages/test-fixtures/foods/dishes.json"
D = Decimal


def _doc_sections() -> dict[int, list[tuple[str, str]]]:
    """section number -> the (fdc_id, grams) pairs of its `- Ingredients:` line. A parenthetical
    alternative ("(or ghee `173412` 5 g)") is not an ingredient: the first-named one is used."""
    out: dict[int, list[tuple[str, str]]] = {}
    for body in re.split(r"^## (?=\d+\.)", DOC.read_text(encoding="utf-8"), flags=re.MULTILINE)[1:]:
        number = int(body.split(".", 1)[0])
        line = next(ln for ln in body.splitlines() if ln.startswith("- Ingredients"))
        line = re.sub(r"\(or [^)]*\)", "", line)
        out[number] = re.findall(r"`(\d{5,6})`(?: \[proxy\])? ([0-9.]+) g", line)
    return out


def test_dishes_match_research_doc():
    doc = _doc_sections()
    data = load_seed_data()
    assert len(doc) == 30 and len(data.dishes) == 30
    assert sorted(d.doc_section for d in data.dishes) == list(range(1, 31))
    for dish in data.dishes:
        got = [(i.fdc_id, i.grams) for i in dish.ingredients if i.fdc_id is not None]
        want = [(fid, D(g)) for fid, g in doc[dish.doc_section]]
        assert got == want, f"{dish.code} (section {dish.doc_section})"


def test_doc_cooked_yields_match_the_yaml():
    text = DOC.read_text(encoding="utf-8")
    data = load_seed_data()
    for body in re.split(r"^## (?=\d+\.)", text, flags=re.MULTILINE)[1:]:
        number = int(body.split(".", 1)[0])
        m = re.search(r"Cooked yield: about (\d+) g", body)
        dish = next(d for d in data.dishes if d.doc_section == number)
        if dish.status == "seeded":
            assert m and dish.cooked_weight_g == D(m.group(1)), dish.code
        elif m:  # blocked dishes keep no yield in the data
            assert dish.status == "blocked", dish.code


def test_seeded_count_21():
    data = load_seed_data()
    assert len(data.seeded_dishes) == 21
    report = report_for(data)
    assert report.dishes_seeded == 21 and len(report.dishes_excluded) == 9
    assert all(reason for reason in report.dishes_excluded.values())


def test_poha_and_paneer_bhurji_blocked():
    data = load_seed_data()
    by = {d.code: d for d in data.dishes}
    for code in ("poha", "paneer_bhurji"):
        assert by[code].status == "blocked"
        assert any(i.fdc_id is None for i in by[code].ingredients)  # the gap ingredient
    assert not {"poha", "paneer_bhurji"} & {d.code for d in data.seeded_dishes}


def test_piece_dishes_need_weighing():
    by = {d.code: d for d in load_seed_data().dishes}
    for code in ("roti", "idli", "dosa_plain", "paratha", "puri", "boiled_egg", "besan_chilla"):
        assert by[code].status == "needs_weighing", code
        assert by[code].cooked_weight_g is None, code


def test_needs_weighing_switches_on_with_cooked_weight(tmp_path):
    copy = tmp_path / "data"
    shutil.copytree(DATA_DIR, copy)
    raw = yaml.safe_load((copy / "indian_dishes.yaml").read_text(encoding="utf-8"))
    roti = next(d for d in raw["dishes"] if d["code"] == "roti")
    roti["cooked_weight_g"] = 45  # a dietitian weighed it
    (copy / "indian_dishes.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    data = load_seed_data(copy)
    assert next(d for d in data.dishes if d.code == "roti").status == "seeded"
    assert len(data.seeded_dishes) == 22
    codes = {r["source_code"] for r in food_rows(data) if r["source"] == "smartnutri_recipe"}
    assert "roti" in codes


def test_dish_nutrient_null_if_any_ingredient_unknown():
    data = load_seed_data()
    foods = {f.fdc_id: f for f in data.foods}
    dal = next(d for d in data.dishes if d.code == "dal_tadka")
    blank = [i.fdc_id for i in dal.ingredients if foods[i.fdc_id].per_100["sugars_g"] is None]
    assert blank == ["172436"]  # toor dal has no sugar_g in the CSV
    per = dish_per_100(dal, foods)
    assert per["sugars_g"] is None  # never a partial sum stored as complete
    assert per["energy_kcal"] is not None and per["protein_g"] is not None
    # A dish whose ingredients all know sugar does have it.
    raita = next(d for d in data.dishes if d.code == "cucumber_raita")
    assert all(foods[i.fdc_id].per_100["sugars_g"] is not None for i in raita.ingredients)
    assert dish_per_100(raita, foods)["sugars_g"] is not None


def test_dish_sat_fat_always_null():
    data = load_seed_data()
    foods = {f.fdc_id: f for f in data.foods}
    assert data.seeded_dishes
    for dish in data.seeded_dishes:
        assert dish_per_100(dish, foods)["sat_fat_g"] is None, dish.code
    for row in food_rows(data):
        assert row["per_100"]["sat_fat_g"] is None


def test_curd_rice_energy_by_hand():
    data = load_seed_data()
    foods = {f.fdc_id: f for f in data.foods}
    curd_rice = next(d for d in data.dishes if d.code == "curd_rice")
    assert [(i.fdc_id, i.grams) for i in curd_rice.ingredients] == [
        ("168878", D("150")),  # rice, cooked
        ("171284", D("120")),  # curd
        ("171265", D("30")),  # milk
        ("173468", D("1")),  # salt
        ("170929", D("0.5")),  # mustard seed
        ("171017", D("3")),  # oil
    ]
    assert curd_rice.cooked_weight_g == D("300")
    total = sum(
        (D(str(foods[i.fdc_id].per_100["energy_kcal"])) * i.grams / 100)
        for i in curd_rice.ingredients
    )
    assert dish_per_100(curd_rice, foods)["energy_kcal"] == total / D("300") * 100
    # Read straight from the CSV, not through the loader.
    import csv

    with (DATA_DIR / "usda_fdc_foods.csv").open(encoding="utf-8", newline="") as fh:
        energy = {r["fdc_id"]: D(r["energy_kcal"]) for r in csv.DictReader(fh)}
    by_hand = sum(energy[i.fdc_id] * i.grams / 100 for i in curd_rice.ingredients) / 300 * 100
    assert dish_per_100(curd_rice, foods)["energy_kcal"] == by_hand


def test_dish_salt_comes_from_sodium():
    data = load_seed_data()
    foods = {f.fdc_id: f for f in data.foods}
    plain_rice = next(d for d in data.dishes if d.code == "plain_rice")
    # Only the rice has sodium: 5 mg per 100 g, 100 g, cooked weight 250 g.
    n = fdc_nutrients(foods["169756"])
    assert n.salt_g is None and n.sodium_mg == 5.0
    salt = dish_per_100(plain_rice, foods)["salt_g"]
    assert salt == D("5") * D("2.5") / 1000 * 100 / 250 * 1  # sodium x 2.5 / 1000, per 100 g
    assert recipe_math.NUTRIENT_KEYS[2] == "salt_g"


def test_dishes_fixture():
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data = load_seed_data()
    foods = {f.fdc_id: f for f in data.foods}
    assert set(expected["dishes"]) == {d.code for d in data.seeded_dishes}
    for dish in data.seeded_dishes:
        want = expected["dishes"][dish.code]
        got = dish_per_100(dish, foods)
        for key in recipe_math.NUTRIENT_KEYS:
            if want["per_100"][key] is None:
                assert got[key] is None, (dish.code, key)
            else:
                assert abs(float(got[key]) - want["per_100"][key]) < 1e-3, (dish.code, key)
    assert expected["excluded"] == {d.code: d.status for d in data.dishes if d.status != "seeded"}

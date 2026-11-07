"""The unit rows: migration 0010 constants = household_units.yaml = the research CSV."""

import csv
import importlib.util
from decimal import Decimal
from pathlib import Path

import yaml

API = Path(__file__).resolve().parents[3]
YAML = API / "app/features/foods/data/household_units.yaml"
CSV = API.parents[1] / "docs/research/food-diary/data/household_units.csv"


def _yaml() -> dict:
    return yaml.safe_load(YAML.read_text(encoding="utf-8"))


def _migration():
    path = API / "alembic/versions/0010_diary_foods_units.py"
    spec = importlib.util.spec_from_file_location("migration_0010", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_rows_equal_yaml():
    rows = tuple((u["code"], u["kind"], u["ml"], u["grams"], u["sort"]) for u in _yaml()["units"])
    assert rows == _migration().UNIT_ROWS
    assert [r[0] for r in rows] == [
        "g", "ml", "serving", "piece", "piece_small", "piece_medium", "piece_large", "roti",
        "slice", "katori", "katori_small", "katori_medium", "katori_large", "cup", "glass",
        "tbsp", "tsp",
    ]  # fmt: skip
    assert [r[4] for r in rows] == list(range(17))


def test_katori_default_200_and_nin_sizes():
    ml = {u["code"]: u["ml"] for u in _yaml()["units"]}
    assert ml["katori"] == "200"  # Q6b: the default is 200 ml, not the old 150
    assert ml["katori_small"] == "115"
    assert ml["katori_medium"] == "155"
    assert ml["katori_large"] == "360"
    assert ml["cup"] == "200" and ml["glass"] == "250" and ml["tbsp"] == "15" and ml["tsp"] == "5"


def test_yaml_values_equal_csv_cells():
    rows = {r["unit_key"]: r for r in csv.DictReader(CSV.open(encoding="utf-8"))}
    checked = 0
    for u in _yaml()["units"]:
        key = u["csv_key"]
        if key is None:
            assert u["ml"] is None and u["grams"] is None  # size words and roti: no value
            continue
        cell = rows[key]
        for col in ("ml", "grams"):
            if u[col] is None:
                assert cell[col] == "", (u["code"], col)
            else:
                assert cell[col] != "", (u["code"], col)
                assert Decimal(u[col]) == Decimal(cell[col]), (u["code"], col)
        checked += 1
    assert checked == 13
    # The superseded CSV katori (150 ml) is not seeded.
    assert rows["katori"]["ml"] == "150"
    assert {n["csv_key"] for n in _yaml()["not_seeded"]} == {
        "katori", "ladle", "handful", "bowl", "plate",
    }  # fmt: skip

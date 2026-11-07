"""The seed data files agree with the research CSVs (Plan 12 Task 3; G3-G6).

Never a seeded number for an empty CSV cell, and every seeded number is its CSV cell.
"""

import csv
from decimal import Decimal
from pathlib import Path

import yaml

from app.features.foods.seed import DATA_DIR, food_rows, load_seed_data

RESEARCH = Path(__file__).resolve().parents[5] / "docs/research/food-diary/data"


def _units_csv() -> dict[str, dict[str, str]]:
    with (RESEARCH / "household_units.csv").open(encoding="utf-8", newline="") as fh:
        return {r["unit_key"]: r for r in csv.DictReader(fh)}


def _yaml(name: str):
    return yaml.safe_load((DATA_DIR / name).read_text(encoding="utf-8"))


def test_fdc_csv_is_byte_copy_of_research():
    assert (DATA_DIR / "usda_fdc_foods.csv").read_bytes() == (
        RESEARCH / "usda_ingredients.csv"
    ).read_bytes()


def test_every_csv_unit_row_classified_once():
    units, portions = _yaml("household_units.yaml"), _yaml("food_portions.yaml")
    keys = (
        [u["csv_key"] for u in units["units"] if u["csv_key"]]
        + [n["csv_key"] for n in units["not_seeded"]]
        + [p["csv_key"] for p in portions["portions"]]
        + [d["csv_key"] for d in portions["densities"]]
        + [n["csv_key"] for n in portions["not_seeded"]]
        + [u["csv_key"] for u in portions["unknown_piece_weights"]]
    )
    assert len(_units_csv()) == 71
    assert len(keys) == len(set(keys)), "a unit_key is classified twice"
    assert set(keys) == set(_units_csv())


def test_no_seeded_number_for_empty_csv_cells():
    """The 12 per-piece rows with no grams get no portion row and no number anywhere."""
    csv_rows = _units_csv()
    data = load_seed_data()
    empty = {
        k
        for k, r in csv_rows.items()
        if r["kind"] == "piece" and not r["grams"] and k not in ("piece", "slice", "serving")
    }
    assert len(empty) == 12
    assert empty == set(data.unknown_piece_weights)
    seeded_portion_keys = {p.csv_key for p in data.portions}
    seeded_density_keys = {d.csv_key for d in data.densities}
    assert not empty & seeded_portion_keys
    assert not empty & seeded_density_keys
    # Every row the loader turns into a number has a non-empty CSV cell for that number.
    for p in data.portions:
        assert csv_rows[p.csv_key]["grams"] != "", p.csv_key
    for d in data.densities:
        assert csv_rows[d.csv_key]["density_g_per_ml"] != "", d.csv_key
    # No unit row carries a value where the CSV cell is empty (ml or grams).
    for u in _yaml("household_units.yaml")["units"]:
        if u["csv_key"] is None:
            continue
        for col in ("ml", "grams"):
            if csv_rows[u["csv_key"]][col] == "":
                assert u[col] is None, (u["code"], col)
    # And the foods the 12 rows name get no portion or density through the seeded food rows.
    portion_units = {(p.fdc_id, p.unit) for p in data.portions}
    assert ("168106", "piece") not in portion_units  # papad: no piece weight


def test_seeded_numbers_equal_csv_cells():
    csv_rows = _units_csv()
    data = load_seed_data()
    assert len(data.portions) == 19 and len(data.densities) == 20
    for p in data.portions:
        row = csv_rows[p.csv_key]
        assert p.fdc_id == row["food_ref_fdc_id"]
        assert p.grams == Decimal(row["grams"])
    for d in data.densities:
        row = csv_rows[d.csv_key]
        assert d.fdc_id == row["food_ref_fdc_id"]
        assert d.density == Decimal(row["density_g_per_ml"])
    assert set(data.not_seeded) == {"naan_plain_commercial", "naan_wholewheat_commercial"}


def test_portion_and_density_fdc_ids_exist():
    data = load_seed_data()
    known = {f.fdc_id for f in data.foods}
    assert len(known) == 141
    assert {p.fdc_id for p in data.portions} <= known
    assert {d.fdc_id for d in data.densities} <= known
    for naan in ("171845", "174077"):
        assert naan not in known  # why naan is not seeded


def test_fdc_blank_cells_stay_null_and_columns_with_no_source_are_null():
    data = load_seed_data()
    rows = {r["source_code"]: r for r in food_rows(data) if r["source"] == "usda_fdc"}
    assert len(rows) == 141
    toor = rows["172436"]["per_100"]  # the CSV has no sugar_g for pigeon peas
    assert toor["sugars_g"] is None and toor["energy_kcal"] == 343.0
    for row in rows.values():
        per = row["per_100"]
        assert per["sat_fat_g"] is None and per["salt_g"] is None and per["fvl_percent"] is None
    assert rows["172437"]["density_g_per_ml"] == Decimal("0.71")
    assert rows["172437"]["density_source"] == "fdc_derived"
    assert rows["172420"]["density_g_per_ml"] is None  # no density row: stays unknown
    assert all(r["licence"] == "CC0 1.0" for r in rows.values())

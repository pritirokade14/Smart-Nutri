"""to_grams and friends (Plan 12 Task 2; spec 5.6 and 9.2). Pure: no database."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.core.errors import ApiError
from app.features.foods.units import (
    FoodUnits,
    default_unit,
    portion_amount,
    resolve_units,
    settable_units,
    table_from_yaml,
    to_grams,
)

D = Decimal
TABLE = table_from_yaml()
FIXTURE = Path(__file__).resolve().parents[5] / "packages/test-fixtures/units/conversions.json"

DAL = FoodUnits("g", density_g_per_ml=D("0.71"))


def u(code: str):
    return TABLE[code]


def test_katori_of_cooked_dal_uses_density():  # 1 katori (200 ml) x 0.71 = 142
    assert to_grams(D("1"), u("katori"), DAL) == D("142.00")


def test_nin_katori_sizes():  # 115 / 155 / 360 ml x 0.71
    assert to_grams(D("1"), u("katori_small"), DAL) == D("81.65")
    assert to_grams(D("1"), u("katori_medium"), DAL) == D("110.05")
    assert to_grams(D("1"), u("katori_large"), DAL) == D("255.6")


def test_user_override_beats_global_beats_density():
    roti = FoodUnits("g", global_portions={"roti": D("68")}, user_portions={"roti": D("35")})
    assert to_grams(D("2"), u("roti"), roti) == D("70")
    glob = FoodUnits("g", global_portions={"roti": D("68")})
    assert to_grams(D("2"), u("roti"), glob) == D("136")
    # A portion row for a volume unit beats the density.
    both = FoodUnits("g", density_g_per_ml=D("0.71"), global_portions={"katori": D("150")})
    assert to_grams(D("1"), u("katori"), both) == D("150")
    both_user = FoodUnits(
        "g",
        density_g_per_ml=D("0.71"),
        global_portions={"katori": D("150")},
        user_portions={"katori": D("120")},
    )
    assert to_grams(D("1"), u("katori"), both_user) == D("120")


def test_serving_needs_serving_g():
    assert to_grams(D("2"), u("serving"), FoodUnits("g")) is None
    assert to_grams(D("2"), u("serving"), FoodUnits("g", serving_g=D("30"))) == D("60")


def test_refuses_count_unit_without_portion():
    food = FoodUnits("g", density_g_per_ml=D("0.9"), serving_g=D("30"))
    for code in ("piece", "roti", "slice", "piece_small", "piece_medium", "piece_large"):
        assert to_grams(D("1"), u(code), food) is None, code


def test_refuses_volume_without_density_on_gram_basis():
    food = FoodUnits("g", serving_g=D("30"), global_portions={"roti": D("68")})
    for code in ("katori", "tbsp", "tsp", "cup", "glass", "ml"):
        assert to_grams(D("1"), u(code), food) is None, code


def test_ml_basis_volume_is_ml():
    milk = FoodUnits("ml")
    assert to_grams(D("1"), u("glass"), milk) == D("250")
    assert to_grams(D("2"), u("katori_small"), milk) == D("230")
    assert to_grams(D("30"), u("ml"), milk) == D("30")


def test_ml_basis_mass_needs_density():
    assert to_grams(D("50"), u("g"), FoodUnits("ml")) is None
    # With a density, 50 g of a 1.031 g/ml food is 50 / 1.031 ml.
    assert to_grams(D("103.1"), u("g"), FoodUnits("ml", density_g_per_ml=D("1.031"))) == D("100")


def test_portion_amount_bounds():
    with pytest.raises(ApiError) as exc:
        portion_amount(D("1001"), "katori", DAL, TABLE)
    assert exc.value.code == "quantity_out_of_range"
    heavy = FoodUnits("g", density_g_per_ml=D("1.0"))
    with pytest.raises(ApiError) as exc:  # 30 x 360 ml x 1.0 = 10800 > 5000
        portion_amount(D("30"), "katori_large", heavy, TABLE)
    assert exc.value.code == "quantity_out_of_range"
    with pytest.raises(ApiError) as exc:
        portion_amount(D("0"), "g", DAL, TABLE)
    assert exc.value.code == "quantity_out_of_range"
    with pytest.raises(ApiError) as exc:
        portion_amount(D("5001"), "g", DAL, TABLE)
    assert exc.value.code == "quantity_out_of_range"
    assert portion_amount(D("5000"), "g", DAL, TABLE) == D("5000")  # g and ml allow 5000
    assert portion_amount(
        D("1000"), "piece", FoodUnits("g", global_portions={"piece": D("1")}), TABLE
    )


def test_portion_amount_refusals():
    with pytest.raises(ApiError) as exc:
        portion_amount(D("1"), "ladle", DAL, TABLE)
    assert (exc.value.code, exc.value.status) == ("unit_not_supported", 422)
    with pytest.raises(ApiError) as exc:
        portion_amount(D("2"), "idli", DAL, TABLE)  # not a unit
    assert exc.value.code == "unit_not_supported"
    with pytest.raises(ApiError) as exc:
        portion_amount(D("2"), "roti", DAL, TABLE)
    assert (exc.value.code, exc.value.status) == ("unit_grams_unknown", 422)


def test_resolve_units_order_and_default():
    codes = [r.code for r in resolve_units(DAL, TABLE)]
    assert codes == [
        "g", "ml", "katori", "katori_small", "katori_medium", "katori_large", "cup", "glass",
        "tbsp", "tsp",
    ]  # fmt: skip
    assert default_unit(resolve_units(DAL, TABLE)) == "katori"
    by = {r.code: r for r in resolve_units(DAL, TABLE)}
    assert by["g"].source == "mass" and by["katori"].source == "density"
    assert by["katori"].grams_per_unit == D("142.00")
    packaged = FoodUnits("g", serving_g=D("30"), global_portions={"roti": D("68")})
    assert [r.code for r in resolve_units(packaged, TABLE)] == ["g", "serving", "roti"]
    assert default_unit(
        resolve_units(FoodUnits("g", global_portions={"roti": D("68")}), TABLE)
    ) == ("roti")
    assert default_unit(resolve_units(packaged, TABLE)) == "serving"
    assert default_unit(resolve_units(FoodUnits("g"), TABLE)) == "g"
    # An ml-basis food: the order is unchanged (katori resolves in ml); `g` needs a density.
    assert default_unit(resolve_units(FoodUnits("ml"), TABLE)) == "katori"
    assert (
        default_unit([r for r in resolve_units(FoodUnits("ml"), TABLE) if r.code == "ml"]) == "ml"
    )


def test_settable_units_excludes_mass_and_serving():
    got = settable_units(FoodUnits("g", serving_g=D("30")), TABLE)
    assert "g" not in got and "serving" not in got
    assert got == [
        "ml", "piece", "piece_small", "piece_medium", "piece_large", "roti", "slice", "katori",
        "katori_small", "katori_medium", "katori_large", "cup", "glass", "tbsp", "tsp",
    ]  # fmt: skip
    # A unit that already resolves is not offered to set.
    assert "katori" not in settable_units(DAL, TABLE)
    assert "roti" not in settable_units(FoodUnits("g", global_portions={"roti": D("68")}), TABLE)


# ---- Hypothesis properties (spec 9.2)

QTY = st.decimals(min_value=D("0.01"), max_value=D("1000"), places=2)
GRAMS = st.decimals(min_value=D("0.1"), max_value=D("2000"), places=1)
DENSITY = st.decimals(min_value=D("0.05"), max_value=D("2"), places=3)
UNIT = st.sampled_from(sorted(TABLE))
NON_MASS = st.sampled_from([c for c, x in sorted(TABLE.items()) if x.kind != "mass"])
CODES = st.sampled_from(sorted(TABLE))


@st.composite
def foods(draw, basis=None):
    return FoodUnits(
        basis=basis or draw(st.sampled_from(["g", "ml"])),
        serving_g=draw(st.none() | GRAMS),
        density_g_per_ml=draw(st.none() | DENSITY),
        global_portions=draw(st.dictionaries(CODES, GRAMS, max_size=4)),
        user_portions=draw(st.dictionaries(CODES, GRAMS, max_size=3)),
    )


@given(foods(basis="g"), UNIT, QTY, st.integers(min_value=1, max_value=20))
def test_linearity(food, code, q, k):
    base = to_grams(q, u(code), food)
    scaled = to_grams(q * k, u(code), food)
    assert (base is None) == (scaled is None)
    if base is not None:
        assert scaled == base * k


@given(foods(basis="g"), UNIT, QTY, QTY)
def test_monotonic(food, code, q1, q2):
    a, b = to_grams(q1, u(code), food), to_grams(q2, u(code), food)
    assert (a is None) == (b is None)
    if a is not None and b is not None and q1 < q2:
        assert a < b


@given(foods(basis="g"), QTY)
def test_mass_unit_ignores_food(food, q):
    assert to_grams(q, u("g"), food) == q


@given(st.dictionaries(CODES, GRAMS, max_size=4), NON_MASS, QTY)
def test_never_returns_quantity_itself(portions, code, q):
    """A gram-basis food with no density: a count or volume unit with no portion row (and
    `serving` with no serving weight) returns None, never the quantity."""
    food = FoodUnits("g", serving_g=None, density_g_per_ml=None, global_portions=portions)
    got = to_grams(q, u(code), food)
    if code in portions and code != "serving":  # serving uses serving_g, never a portion row
        assert got == q * portions[code]
    else:
        assert got is None


@given(foods(), UNIT, QTY)
def test_result_positive_when_resolved(food, code, q):
    got = to_grams(q, u(code), food)
    if got is not None:
        assert got > 0


@given(foods(), UNIT)
def test_resolved_units_are_exactly_those_that_convert(food, code):
    resolved = {r.code: r for r in resolve_units(food, TABLE)}
    one = to_grams(D(1), u(code), food)
    assert (code in resolved) == (one is not None)
    if one is not None:
        assert resolved[code].grams_per_unit == one
    assert not set(settable_units(food, TABLE)) & set(resolved)


def _case_food(raw: dict) -> FoodUnits:
    def dec(v):
        return None if v is None else D(str(v))

    return FoodUnits(
        raw["basis"],
        serving_g=dec(raw.get("serving_g")),
        density_g_per_ml=dec(raw.get("density_g_per_ml")),
        global_portions={k: D(str(v)) for k, v in (raw.get("global_portions") or {}).items()},
        user_portions={k: D(str(v)) for k, v in (raw.get("user_portions") or {}).items()},
    )


def test_conversions_fixture():
    from app.features.meals.service import _portion, _round1

    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    assert len(cases) >= 18
    for case in cases:
        food = _case_food(case["food"])
        q, exp = D(str(case["quantity"])), case["expected"]
        one = to_grams(D(1), TABLE[case["unit"]], food)
        assert (None if one is None else float(one)) == exp["grams_per_unit"], case["case"]
        try:
            amount = portion_amount(q, case["unit"], food, TABLE)
        except ApiError as err:
            assert exp["error"] == err.code and exp["amount"] is None, case["case"]
            assert exp["preview"] is None, case["case"]
            continue
        assert exp["error"] is None, case["case"]
        assert float(amount) == exp["amount"], case["case"]
        preview = {
            k: None if v is None else _round1(_portion(v, float(amount)))
            for k, v in case["per_100"].items()
        }
        assert preview == exp["preview"], case["case"]


def test_ml_basis_food_volume_stays_volume_even_with_a_density():
    """Slice-3 fix: an ml-basis food's volume is already millilitres, so no density multiplies it."""
    food = FoodUnits("ml", density_g_per_ml=D("1.05"))
    assert to_grams(D(200), u("ml"), food) == D(200)

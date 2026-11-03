import pytest

from app.scoring import DailyLimits, Member, daily_limits_for, nutrient_band

# --- plan tests --------------------------------------------------------------------------


def test_adult_limits_with_weight(cfg):
    lim = daily_limits_for(Member(id="a", name="A", age=40), 70.0, cfg)
    assert (lim.sugar_g, lim.salt_g, lim.protein_target_g, lim.kcal) == (
        25,
        5,
        pytest.approx(58.1),
        None,
    )


def test_child_bands(cfg):
    lim = daily_limits_for(Member(id="c", name="C", age=8), None, cfg)
    assert (lim.sugar_g, lim.salt_g, lim.protein_target_g) == (24, 5, None)


def test_infant_zero_limits(cfg):
    assert daily_limits_for(Member(id="i", name="I", age=1), None, cfg).sugar_g == 0


def test_bands(cfg):
    assert [nutrient_band(v, 25, cfg) for v in (10, 20, 26, None)] == [
        "ok",
        "near",
        "over",
        "unknown",
    ]
    assert nutrient_band(1, 0, cfg) == "over" and nutrient_band(0, 0, cfg) == "ok"


# --- edges -------------------------------------------------------------------------------


def _limits(age, weight=None, cfg=None):
    return daily_limits_for(Member(id="x", name="X", age=age), weight, cfg)


def test_age_unknown_uses_adult_limits(cfg):
    assert _limits(None, None, cfg) == DailyLimits(
        sugar_g=25, salt_g=5, protein_target_g=None, kcal=None
    )


@pytest.mark.parametrize(
    ("age", "sugar", "salt"),
    [
        (0, 0, 0),
        (1, 0, 0),
        (2, 19, 2),  # NHS: 1-3 years 2 g salt a day (Ruling P6-R1)
        (3, 19, 2),
        (4, 19, 3),
        (6, 19, 3),
        (7, 24, 5),
        (10, 24, 5),
        (11, 30, 6),
        (12, 30, 6),
        (13, 25, 5),  # child.max_age: adult limits from 13
    ],
)
def test_age_bands(cfg, age, sugar, salt):
    lim = _limits(age, None, cfg)
    assert (lim.sugar_g, lim.salt_g) == (sugar, salt)


def test_protein_target_needs_weight_and_rounds(cfg):
    assert _limits(40, None, cfg).protein_target_g is None
    assert _limits(8, 25.0, cfg).protein_target_g == pytest.approx(20.75)


def test_band_edges(cfg):
    # near_pct = 80: exactly 80 % of the limit is near, exactly the limit is not over.
    assert nutrient_band(20, 25, cfg) == "near"
    assert nutrient_band(19.99, 25, cfg) == "ok"
    assert nutrient_band(25, 25, cfg) == "near"
    assert nutrient_band(25.01, 25, cfg) == "over"
    assert nutrient_band(10, None, cfg) == "unknown"
    assert nutrient_band(None, None, cfg) == "unknown"


def test_limits_are_read_from_yaml(cfg):
    dl = cfg.thresholds["daily_limits"]
    assert dl["adult"] == {"sugar_g": 25, "salt_g": 5, "protein_g_per_kg": 0.83}
    assert dl["infant"] == {"sugar_g": 0, "salt_g": 0}
    assert dl["near_pct"] == 80

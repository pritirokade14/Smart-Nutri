from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.core.time import IST as FIXED_IST
from app.features.meals.models import MealLog
from app.features.meals.service import snapshot, to_meal_out
from app.features.meals.summary import NUTRIENTS, summarise
from app.scoring import DailyLimits, Nutrients, load_config

IST = ZoneInfo("Asia/Kolkata")
TODAY = date(2026, 11, 3)
MEMBER = uuid4()
ADULT_LIMITS = DailyLimits(sugar_g=25, salt_g=5, protein_target_g=58.1, kcal=None)


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def meal(*, eaten_at=None, day=TODAY, sugars=0.0, kcal=0.0, salt=0.0, protein=0.0):
    if eaten_at is None:
        eaten_at = datetime.combine(day, time(13, 0), tzinfo=IST)
    return MealLog(
        id=uuid4(),
        member_id=MEMBER,
        grams=50,
        eaten_at=eaten_at,
        nutrients={
            "energy_kcal": kcal,
            "sugars_g": sugars,
            "salt_g": salt,
            "protein_g": protein,
            "fat_g": None,
            "sat_fat_g": None,
            "carbs_g": None,
        },
    )


# --- plan tests --------------------------------------------------------------------------


def test_ist_day_boundary(cfg):
    m = meal(eaten_at=datetime(2026, 11, 3, 18, 0, tzinfo=UTC), sugars=10)  # 23:30 IST, 3 Nov
    s = summarise([m], ADULT_LIMITS, "day", date(2026, 11, 3), IST, cfg, member_id=MEMBER)
    assert s.totals.sugars_g == 10 and s.days[0].date == date(2026, 11, 3)


def test_missing_nutrient_marks_incomplete(cfg):
    s = summarise(
        [meal(sugars=None, kcal=100), meal(sugars=5, kcal=100)],
        ADULT_LIMITS,
        "day",
        TODAY,
        IST,
        cfg,
        member_id=MEMBER,
    )
    assert s.totals.sugars_g == 5 and s.incomplete.sugars_g is True
    assert s.incomplete.energy_kcal is False


def test_week_has_seven_zero_filled_days(cfg):
    s = summarise(
        [meal(day=TODAY, sugars=30)], ADULT_LIMITS, "week", TODAY, IST, cfg, member_id=MEMBER
    )
    assert len(s.days) == 7 and s.days[-1].totals.sugars_g == 30
    # An empty day has no known value: null, never 0.0 (Ruling M1 S1).
    assert s.days[0].totals.sugars_g is None and s.days[0].items == 0


def test_day_band_over_limit(cfg):
    s = summarise([meal(sugars=30)], ADULT_LIMITS, "day", TODAY, IST, cfg, member_id=MEMBER)
    assert s.bands.sugar_g == "over"


# --- more ---------------------------------------------------------------------------------


def _day(meals, limits=ADULT_LIMITS, cfg=None):
    return summarise(meals, limits, "day", TODAY, IST, cfg, member_id=MEMBER)


def test_previous_ist_day_is_excluded(cfg):
    # 18:31 UTC on 2 Nov = 00:01 IST on 3 Nov (in); 18:29 UTC = 23:59 IST on 2 Nov (out).
    inside = meal(eaten_at=datetime(2026, 11, 2, 18, 31, tzinfo=UTC), sugars=4)
    outside = meal(eaten_at=datetime(2026, 11, 2, 18, 29, tzinfo=UTC), sugars=7)
    s = _day([inside, outside], cfg=cfg)
    assert (s.totals.sugars_g, s.days[0].items) == (4, 1)


def test_fixed_offset_ist_matches_zoneinfo(cfg):
    m = meal(eaten_at=datetime(2026, 11, 3, 18, 0, tzinfo=UTC), sugars=10)
    a = summarise([m], ADULT_LIMITS, "day", TODAY, IST, cfg, member_id=MEMBER)
    b = summarise([m], ADULT_LIMITS, "day", TODAY, FIXED_IST, cfg, member_id=MEMBER)
    assert a == b


def test_incomplete_below_limit_is_unknown_never_ok(cfg):
    s = _day([meal(sugars=None), meal(sugars=2)], cfg=cfg)
    assert s.bands.sugar_g == "unknown"
    assert s.days[0].bands.sugar_g == "unknown"


def test_incomplete_but_already_over_stays_over(cfg):
    s = _day([meal(sugars=None), meal(sugars=26)], cfg=cfg)
    assert s.bands.sugar_g == "over"


def test_nothing_logged_is_unknown(cfg):
    s = _day([], cfg=cfg)
    assert set(s.bands.model_dump().values()) == {"unknown"}
    assert s.days[0].items == 0


def test_week_bands_with_every_day_logged_use_seven_times_the_limit(cfg):
    meals = [meal(day=TODAY - timedelta(days=i), sugars=20) for i in range(7)]  # 140 g
    s = summarise(meals, ADULT_LIMITS, "week", TODAY, IST, cfg, member_id=MEMBER)
    assert s.totals.sugars_g == 140 and s.bands.sugar_g == "near"  # 140 >= 0.8 x 175
    assert all(d.bands.sugar_g == "near" for d in s.days)  # 20 >= 0.8 x 25
    assert (s.start, s.end) == (TODAY - timedelta(days=6), TODAY)


def test_protein_is_a_target_never_over(cfg):
    s = _day([meal(protein=80)], cfg=cfg)
    assert s.bands.protein_g == "ok"
    # Below the target there is no band (Ruling M1 S2): never "near", never "ok" at 5 %.
    assert _day([meal(protein=50)], cfg=cfg).bands.protein_g == "unknown"
    # Incomplete and not yet met: unknown. Incomplete but already met: ok.
    assert _day([meal(protein=None), meal(protein=10)], cfg=cfg).bands.protein_g == "unknown"
    assert _day([meal(protein=None), meal(protein=60)], cfg=cfg).bands.protein_g == "ok"


def test_unknown_limits(cfg):
    limits = DailyLimits(sugar_g=25, salt_g=5, protein_target_g=None, kcal=None)
    s = _day([meal(protein=80, kcal=900)], limits, cfg)
    assert (s.bands.protein_g, s.bands.kcal) == ("unknown", "unknown")
    assert s.limits.model_dump() == {
        "sugar_g": 25,
        "salt_g": 5,
        "protein_target_g": None,
        "kcal": None,
        "protein_g_per_kg": None,
    }


def week(meals, limits=ADULT_LIMITS, cfg=None):
    return summarise(meals, limits, "week", TODAY, IST, cfg, member_id=MEMBER)


# --- Ruling M1 (nutrition-safety review of Plan 6) ----------------------------------------


def test_b1_one_over_day_and_six_empty_days_is_over(cfg):
    # The reviewer's probe: 60 g sugar and 9 g salt on one day, nothing else logged.
    s = week([meal(sugars=60, salt=9, protein=10, kcal=500)], cfg=cfg)
    assert s.days[-1].bands.sugar_g == "over" and s.days[-1].bands.salt_g == "over"
    assert (s.bands.sugar_g, s.bands.salt_g) == ("over", "over")


def test_b1_week_limit_is_daily_limit_times_logged_days(cfg):
    # Two logged days of 22 g: 44 g against 2 x 25 g = 50 g is near, not ok against 175 g.
    meals = [meal(day=TODAY, sugars=22), meal(day=TODAY - timedelta(days=3), sugars=22)]
    s = week(meals, cfg=cfg)
    assert s.bands.sugar_g == "near"
    # Two logged days of 10 g: 20 g against 50 g is ok.
    meals = [meal(day=TODAY, sugars=10), meal(day=TODAY - timedelta(days=3), sugars=10)]
    assert week(meals, cfg=cfg).bands.sugar_g == "ok"


def test_b1_any_over_day_forces_the_week_over(cfg):
    # 30 g on one day (over 25 g), 1 g on six days: 36 g is under 7 x 25 g, but a day is over.
    meals = [meal(day=TODAY, sugars=30)]
    meals += [meal(day=TODAY - timedelta(days=i), sugars=1) for i in range(1, 7)]
    s = week(meals, cfg=cfg)
    assert s.days[-1].bands.sugar_g == "over" and s.bands.sugar_g == "over"


def test_b1_over_day_wins_over_an_incomplete_week(cfg):
    meals = [meal(day=TODAY, sugars=30), meal(day=TODAY - timedelta(days=1), sugars=None)]
    s = week(meals, cfg=cfg)
    assert s.incomplete.sugars_g is True and s.bands.sugar_g == "over"


def test_b1_empty_week_is_unknown(cfg):
    s = week([], cfg=cfg)
    assert set(s.bands.model_dump().values()) == {"unknown"}


def test_s1_totals_are_null_when_no_meal_has_a_value(cfg):
    # The reviewer's probe: every meal lacks sugars -> null, not 0.0.
    s = _day([meal(sugars=None, salt=1, protein=10, kcal=500)], cfg=cfg)
    assert s.totals.sugars_g is None and s.incomplete.sugars_g is True
    assert s.bands.sugar_g == "unknown"
    assert (s.totals.salt_g, s.totals.energy_kcal) == (1.0, 500.0)
    # One known value: the total is that value (a lower bound, marked incomplete).
    s = _day([meal(sugars=None), meal(sugars=0)], cfg=cfg)
    assert s.totals.sugars_g == 0.0 and s.incomplete.sugars_g is True


def test_s1_nothing_logged_has_null_totals(cfg):
    s = _day([], cfg=cfg)
    assert s.totals.model_dump() == dict.fromkeys(NUTRIENTS)
    assert s.days[0].totals.model_dump() == dict.fromkeys(NUTRIENTS)
    w = week([meal(sugars=5)], cfg=cfg)
    assert w.totals.sugars_g == 5 and w.totals.salt_g == 0.0
    assert all(d.totals.sugars_g is None for d in w.days[:-1])


def test_s2_protein_below_target_has_no_band(cfg):
    # The reviewer's probe: 5 g of a 58.1 g target is not "within limit".
    assert _day([meal(protein=5)], cfg=cfg).bands.protein_g == "unknown"
    assert _day([meal(protein=58)], cfg=cfg).bands.protein_g == "unknown"
    assert _day([meal(protein=58.1)], cfg=cfg).bands.protein_g == "ok"  # met
    assert _day([meal(protein=None)], cfg=cfg).bands.protein_g == "unknown"


def test_s2_week_protein_target_is_per_logged_day(cfg):
    # Two logged days of 60 g: 120 g meets 2 x 58.1 g; each day meets its own target.
    meals = [meal(day=TODAY, protein=60), meal(day=TODAY - timedelta(days=2), protein=60)]
    s = week(meals, cfg=cfg)
    assert s.bands.protein_g == "ok" and s.days[-1].bands.protein_g == "ok"
    meals = [meal(day=TODAY, protein=60), meal(day=TODAY - timedelta(days=2), protein=50)]
    assert week(meals, cfg=cfg).bands.protein_g == "unknown"  # 110 g < 116.2 g


def test_totals_are_rounded_sums(cfg):
    s = _day([meal(salt=0.1), meal(salt=0.2)], cfg=cfg)
    assert s.totals.salt_g == 0.3


def test_infant_any_sugar_is_over(cfg):
    infant = DailyLimits(sugar_g=0, salt_g=0, protein_target_g=None, kcal=None)
    s = _day([meal(sugars=0.5, salt=0)], infant, cfg)
    assert (s.bands.sugar_g, s.bands.salt_g) == ("over", "ok")


def test_bad_period_rejected(cfg):
    with pytest.raises(ValueError):
        summarise([], ADULT_LIMITS, "month", TODAY, IST, cfg, member_id=MEMBER)


def test_nutrient_keys():
    assert NUTRIENTS == ("energy_kcal", "sugars_g", "salt_g", "protein_g")


# --- cleanup c1: bands compare the UNROUNDED totals -------------------------------------


def test_band_uses_unrounded_total_day(cfg):
    """25.04 g shows as 25.0 g, but it is above a 25 g limit: the band is ``over``."""
    s = summarise([meal(sugars=25.04)], ADULT_LIMITS, "day", TODAY, IST, cfg, member_id=MEMBER)
    assert s.totals.sugars_g == 25.0
    assert s.days[0].bands.sugar_g == "over"
    assert s.bands.sugar_g == "over"


def test_band_uses_unrounded_total_split_meals(cfg):
    s = summarise(
        [meal(sugars=12.52, salt=2.52), meal(sugars=12.52, salt=2.52)],
        ADULT_LIMITS,
        "day",
        TODAY,
        IST,
        cfg,
        member_id=MEMBER,
    )
    assert s.totals.sugars_g == 25.0 and s.totals.salt_g == 5.0
    assert s.days[0].bands.sugar_g == "over"
    assert s.days[0].bands.salt_g == "over"


def test_unrounded_sum_has_no_float_drift(cfg):
    """0.1 + 16.1 + 8.8 is exactly 25 g (float sum: 25.000000000000004): ``near``, not ``over``."""
    s = summarise(
        [meal(sugars=0.1), meal(sugars=16.1), meal(sugars=8.8)],
        ADULT_LIMITS,
        "day",
        TODAY,
        IST,
        cfg,
        member_id=MEMBER,
    )
    assert s.totals.sugars_g == 25.0
    assert s.days[0].bands.sugar_g == "near"


def test_period_band_uses_unrounded_total(cfg):
    """Week: 2 logged days x 25 g = 50 g; 50.04 g rounds to 50.0 but is over."""
    meals = [meal(day=TODAY, sugars=25.0), meal(day=TODAY - timedelta(days=1), sugars=25.04)]
    s = summarise(meals, ADULT_LIMITS, "week", TODAY, IST, cfg, member_id=MEMBER)
    assert s.totals.sugars_g == 50.0
    assert s.bands.sugar_g == "over"


# --- F1: portions are stored unrounded; only display rounds --------------------------------


def _logged(per_100g: Nutrients, grams: float) -> MealLog:
    """A meal log as log_meal stores it: the snapshot of the portion."""
    return MealLog(
        id=uuid4(),
        member_id=MEMBER,
        grams=grams,
        eaten_at=datetime.combine(TODAY, time(13, 0), tzinfo=IST),
        nutrients=snapshot(per_100g, grams).model_dump(),
    )


def test_f1_snapshot_keeps_the_exact_portion():
    s = snapshot(Nutrients(sugars_g=10.016, salt_g=0.8), 250)
    assert (s.sugars_g, s.salt_g) == (25.04, 2.0)  # exact, no float drift
    assert snapshot(Nutrients(salt_g=0.8), 5).salt_g == 0.04


def test_f1_250_g_at_10_016_per_100_g_is_over_25_g(cfg):
    """25.04 g of sugar displays as 25.0 g but is over the 25 g adult limit."""
    s = _day([_logged(Nutrients(sugars_g=10.016, salt_g=0), 250)], cfg=cfg)
    assert s.totals.sugars_g == 25.0
    assert s.days[0].bands.sugar_g == "over" and s.bands.sugar_g == "over"


def test_f1_infant_5_g_at_0_8_salt_per_100_g_is_over(cfg):
    """0.04 g of salt rounded to 0.0 at log time used to read as ``ok`` under the infant
    "no added salt" limit (0 g). Stored unrounded, it is ``over``."""
    infant = DailyLimits(sugar_g=0, salt_g=0, protein_target_g=None, kcal=None)
    s = _day([_logged(Nutrients(sugars_g=0, salt_g=0.8), 5)], infant, cfg)
    assert s.totals.salt_g == 0.0  # display only
    assert s.days[0].bands.salt_g == "over" and s.bands.salt_g == "over"


def test_f1_meal_out_rounds_for_display():
    row = _logged(Nutrients(energy_kcal=401.4, sugars_g=10.016, salt_g=0.9, protein_g=None), 250)
    row.product_name, row.grade, row.client_id = "Biscuit", None, None
    row.product_id, row.off_barcode = uuid4(), None
    out = to_meal_out(row)
    assert (out.nutrients.energy_kcal, out.nutrients.sugars_g, out.nutrients.salt_g) == (
        1003.5,
        25.0,
        2.3,  # 2.25, ROUND_HALF_UP
    )
    assert out.nutrients.protein_g is None  # never 0
    assert row.nutrients["sugars_g"] == 25.04  # the stored value is untouched


def test_protein_target_uses_unrounded_total(cfg):
    """58.06 g displays as 58.1 g but is below a 58.1 g target: no band, never ``ok``."""
    s = summarise([meal(protein=58.06)], ADULT_LIMITS, "day", TODAY, IST, cfg, member_id=MEMBER)
    assert s.totals.protein_g == 58.1
    assert s.days[0].bands.protein_g == "unknown"

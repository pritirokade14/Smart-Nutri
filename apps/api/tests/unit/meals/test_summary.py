from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.core.time import IST as FIXED_IST
from app.features.meals.models import MealLog
from app.features.meals.summary import NUTRIENTS, summarise
from app.scoring import DailyLimits, load_config

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
    assert len(s.days) == 7 and s.days[-1].totals.sugars_g == 30 and s.days[0].totals.sugars_g == 0


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


def test_week_bands_use_seven_times_the_limit(cfg):
    meals = [meal(day=TODAY - timedelta(days=i), sugars=20) for i in range(7)]  # 140 g
    s = summarise(meals, ADULT_LIMITS, "week", TODAY, IST, cfg, member_id=MEMBER)
    assert s.totals.sugars_g == 140 and s.bands.sugar_g == "near"  # 140 >= 0.8 x 175
    assert all(d.bands.sugar_g == "near" for d in s.days)  # 20 >= 0.8 x 25
    assert (s.start, s.end) == (TODAY - timedelta(days=6), TODAY)


def test_protein_is_a_target_never_over(cfg):
    s = _day([meal(protein=80)], cfg=cfg)
    assert s.bands.protein_g == "ok"
    assert _day([meal(protein=50)], cfg=cfg).bands.protein_g == "near"
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
    }


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

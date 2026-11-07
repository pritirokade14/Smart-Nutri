"""Daily-targets engine (Plan 10 Task 1): golden examples G1-G12 from the Food Diary spec
section 4.12, boundaries, safety rails and settings rules."""

from __future__ import annotations

import copy
import dataclasses
from decimal import Decimal

import pytest

from app.scoring import targets as T
from app.scoring.config import load_config


def D(x) -> Decimal:
    return Decimal(str(x))


def body(**kw) -> T.BodyData:
    base = {
        "age": 28,
        "sex": "male",
        "height_cm": D(175),
        "weight_kg": D(70),
        "body_fat_pct": None,
        "goal": None,
    }
    base.update(
        {
            k: (D(v) if k in {"height_cm", "weight_kg", "body_fat_pct"} and v is not None else v)
            for k, v in kw.items()
        }
    )
    return T.BodyData(**base)


def settings(direction="maintain", activity="moderate", **kw) -> T.GoalSettings:
    for k in ("rate_pct_bw_per_week", "target_weight_kg", "fat_pct_energy"):
        if kw.get(k) is not None:
            kw[k] = D(kw[k])
    return T.GoalSettings(direction=direction, activity_level=activity, **kw)


G1 = (body(goal="build_muscle"), settings("gain", "moderate", rate_pct_bw_per_week=0.25))
G2 = (
    body(age=40, sex="female", height_cm=160, weight_kg=80, goal="weight_loss"),
    settings("lose", "light", rate_pct_bw_per_week=0.5),
)
G3 = (
    body(age=30, sex="female", height_cm=155, weight_kg=55, goal="healthy_eating"),
    settings("maintain", "sedentary"),
)
G4 = (
    body(age=55, sex="female", height_cm=150, weight_kg=52, goal="weight_loss"),
    settings("lose", "sedentary", rate_pct_bw_per_week=1.0),
)
G5 = (  # W = 76.2, the trend value (Ruling D18)
    body(age=35, sex="male", height_cm=170, weight_kg=76.2, goal="weight_loss"),
    settings("lose", "light", rate_pct_bw_per_week=0.75, target_weight_kg=75),
)
G8 = (
    body(age=30, sex="other", height_cm=165, weight_kg=60, goal="healthy_eating"),
    settings("maintain", "moderate"),
)
G11 = (dataclasses.replace(G1[0], body_fat_pct=D(15)), G1[1])
G12 = (dataclasses.replace(G2[0], body_fat_pct=D(38)), G2[1])
ALL = {"G1": G1, "G2": G2, "G3": G3, "G4": G4, "G5": G5, "G8": G8, "G11": G11, "G12": G12}


@pytest.mark.parametrize(
    "case, energy, p, f, c, basis, flags",
    [
        ("G1", 2760, 112, 77, 405, "actual_weight", ()),
        ("G2", 1540, 71, 43, 217, "adjusted_weight", ()),
        ("G3", 1450, 46, 40, 227, "actual_weight", ()),
        ("G4", 1200, 62, 33, 164, "actual_weight", ("deficit_capped", "floor_applied")),
        ("G5", 1940, 91, 54, 273, "actual_weight", ("taper_active",)),
        ("G8", 2180, 50, 61, 358, "actual_weight", ("average_sex_reference",)),
        ("G11", 2760, 119, 77, 398, "lean_mass", ()),
        ("G12", 1540, 74, 43, 214, "lean_mass", ()),
    ],
)
def test_golden_examples(case, energy, p, f, c, basis, flags):
    r = T.compute(*ALL[case])
    assert r.status == "ready"
    assert (r.energy_kcal, r.protein_g, r.fat_g, r.carbs_g) == (energy, p, f, c)
    assert r.explanation.protein_basis == basis
    assert r.flags == flags


def test_g1_explanation():
    e = T.compute(*G1).explanation
    assert e.bmr_kcal == D("1658.75")
    assert e.maintenance_kcal == D("2571.0625")
    assert e.adjustment_kcal == D("192.5")
    assert e.activity_factor == D("1.55")
    assert e.floor_kcal is None
    assert e.weight_kg_used == D(70)


def test_g2_adjusted_weight():
    e = T.compute(*G2).explanation
    assert e.ibw_kg.quantize(D("0.0001")) == D("52.3819")
    assert e.protein_reference_weight_kg.quantize(D("0.0001")) == D("59.2864")
    assert e.protein_g_per_kg == D("1.2")
    assert e.floor_kcal == D(1439)


def test_g4_floor_and_deficit_cap():
    e = T.compute(*G4).explanation
    assert e.adjustment_kcal == D("-306.45")
    assert e.floor_kcal == D(1200)


def test_g5_taper_rate():
    r = T.compute(*G5)
    assert r.rate.kg_per_week == D("0.3")
    assert r.explanation.adjustment_kcal == D(-330)


def test_g6_minor_has_no_targets():
    r = T.compute(body(age=16), settings("maintain"))
    assert r.status == "not_available_minor"
    assert r.energy_kcal is None and r.protein_g is None and r.fat_g is None
    assert r.carbs_g is None and r.explanation is None


def test_g7_underweight_lose_refused():
    b = body(height_cm=168, weight_kg=50, goal="weight_loss")
    with pytest.raises(T.SettingsRuleError) as e:
        T.check_settings(b, settings("lose"))
    assert e.value.code == "goal_not_allowed_underweight"


def test_macros_add_up_within_2_kcal():
    for name, (b, s) in ALL.items():
        r = T.compute(b, s)
        assert abs(4 * r.protein_g + 9 * r.fat_g + 4 * r.carbs_g - r.energy_kcal) <= 2, name


def test_bmi_boundary_is_exact():
    s = settings("maintain")
    below = T.compute(body(height_cm=160, weight_kg="76.5"), s)
    at = T.compute(body(height_cm=160, weight_kg="76.8"), s)  # BMI exactly 30.0
    assert below.explanation.protein_basis == "actual_weight"
    assert at.explanation.protein_basis == "adjusted_weight"


def test_body_fat_wins_over_bmi():
    r = T.compute(*G12)  # BMI 31.25
    assert r.explanation.protein_basis == "lean_mass"
    assert r.explanation.body_fat_pct_used == D(38)
    assert r.explanation.ibw_kg is None


def test_body_fat_bounds():
    for bad in ("2.9", "70.1"):
        with pytest.raises(T.SettingsRuleError) as e:
            T.check_body_fat(D(bad))
        assert e.value.code == "body_fat_out_of_range"
        assert e.value.details == {"min": 3, "max": 70}
    for ok in ("3", "70", None):
        T.check_body_fat(None if ok is None else D(ok))


@pytest.mark.parametrize(
    "sex, expected",
    [("male", "70.46"), ("female", "65.96"), ("other", "68.21")],
)
def test_devine_ibw(sex, expected):
    r = T.compute(body(sex=sex, height_cm=175, weight_kg=100), settings("maintain"))
    assert r.explanation.ibw_kg.quantize(D("0.01")) == D(expected)


def test_devine_short_height_is_base_only():
    r = T.compute(body(sex="female", height_cm=150, weight_kg=75), settings("maintain"))
    assert r.explanation.protein_basis == "adjusted_weight"  # BMI 33.3
    assert r.explanation.ibw_kg == D("45.5")


@pytest.mark.parametrize(
    "goal, factor",
    [
        ("build_muscle", "2.0"),
        ("weight_loss", "1.5"),
        ("healthy_eating", "1.0"),
        ("weight_gain", "1.0"),
        (None, "1.0"),
    ],
)
def test_lean_mass_factor_every_goal(goal, factor):
    r = T.compute(body(goal=goal, body_fat_pct=20), settings("maintain"))
    assert r.explanation.protein_basis == "lean_mass"
    assert r.explanation.protein_g_per_kg == D(factor)


@pytest.mark.parametrize(
    "goal, per_kg",
    [
        ("build_muscle", "1.6"),
        ("weight_loss", "1.2"),
        ("healthy_eating", "0.83"),
        ("weight_gain", "0.83"),
        (None, "0.83"),
    ],
)
def test_protein_g_per_kg_by_goal(goal, per_kg):
    assert T.protein_g_per_kg(goal) == D(per_kg)
    r = T.compute(body(goal=goal), settings("maintain"))
    assert r.explanation.protein_g_per_kg == D(per_kg)


def test_age_bounds():
    s = settings("maintain")
    assert T.compute(body(age=17), s).status == "not_available_minor"
    r18 = T.compute(body(age=18), s)
    assert r18.status == "ready" and "outside_equation_age_range" not in r18.flags
    assert "outside_equation_age_range" not in T.compute(body(age=78), s).flags
    assert "outside_equation_age_range" in T.compute(body(age=79), s).flags


@pytest.mark.parametrize("missing", ["birth_year", "sex", "height_cm", "weight_kg"])
def test_needs_body_data_each_field(missing):
    kw = {"birth_year": "age"}.get(missing, missing)
    r = T.compute(body(**{kw: None}), settings("maintain"))
    assert r.status == "needs_body_data"
    assert r.missing_fields == (missing,)
    assert r.energy_kcal is None and r.explanation is None


def test_needs_body_data_lists_every_missing_field():
    r = T.compute(body(age=None, height_cm=None), settings("maintain"))
    assert r.missing_fields == ("birth_year", "height_cm")


def test_pregnancy_pauses():
    r = T.compute(body(height_cm=None), settings("maintain", pregnant_or_breastfeeding=True))
    assert r.status == "paused_pregnancy"
    assert r.energy_kcal is None


def test_floor_binds_for_each_sex():
    male = T.compute(
        body(age=70, sex="male", height_cm=160, weight_kg=60),
        settings("lose", "sedentary", rate_pct_bw_per_week=1.0),
    )
    assert male.energy_kcal == 1500 and "floor_applied" in male.flags
    avg = T.compute(
        body(age=45, sex="other", height_cm=160, weight_kg=65),
        settings("lose", "light", rate_pct_bw_per_week=1.0),
    )
    assert avg.energy_kcal == 1500 and "floor_applied" in avg.flags


def test_floor_limits_deficit_targets_maintenance():
    r = T.compute(
        body(age=75, sex="female", height_cm=145, weight_kg=48),
        settings("lose", "sedentary", rate_pct_bw_per_week=0.5),
    )
    assert r.energy_kcal == 1020  # maintenance 1020.3
    assert "floor_limits_deficit" in r.flags and "floor_applied" not in r.flags


def test_deficit_cap_at_1000():
    r = T.compute(
        body(age=25, sex="male", height_cm=190, weight_kg=130),
        settings("lose", "very", rate_pct_bw_per_week=1.0),
    )
    assert r.explanation.adjustment_kcal == D(-1000)
    assert "rate_capped" in r.flags and "deficit_capped" in r.flags


def test_max_kg_per_week():
    r = T.compute(
        body(age=30, sex="male", height_cm=175, weight_kg=120),
        settings("lose", "moderate", rate_pct_bw_per_week=1.0),
    )
    assert r.rate.kg_per_week == D("1.0")
    assert "rate_capped" in r.flags


def test_rate_clamped_to_options_range():
    r = T.compute(body(weight_kg=80), settings("lose", "moderate", rate_pct_bw_per_week=1.5))
    assert r.rate.pct_bw_per_week == D("1.0")
    assert "rate_capped" in r.flags


def test_default_rate_when_none():
    r = T.compute(body(weight_kg=80), settings("lose", "moderate"))
    assert r.rate.pct_bw_per_week == D("0.5")
    g = T.compute(body(weight_kg=80), settings("gain", "moderate"))
    assert g.rate.pct_bw_per_week == D("0.25")
    assert T.compute(body(), settings("maintain")).rate is None


def test_taper_band_reaches_maintenance():
    r = T.compute(
        body(weight_kg="75.4"),
        settings("lose", "moderate", rate_pct_bw_per_week=0.5, target_weight_kg=75),
    )
    assert r.explanation.adjustment_kcal == 0
    assert "goal_weight_reached" in r.flags
    assert r.rate is None


def test_taper_past_target():
    r = T.compute(
        body(weight_kg=74),
        settings("lose", "moderate", rate_pct_bw_per_week=0.5, target_weight_kg=75),
    )
    assert r.explanation.adjustment_kcal == 0 and "goal_weight_reached" in r.flags


def test_gain_taper_reaches_target():
    r = T.compute(
        body(weight_kg="70.2"),
        settings("gain", "moderate", rate_pct_bw_per_week=0.25, target_weight_kg=70.5),
    )
    assert "goal_weight_reached" in r.flags and r.explanation.adjustment_kcal == 0


def test_protein_capped_at_energy_share():
    r = T.compute(
        body(age=70, sex="male", height_cm=160, weight_kg=100, goal="build_muscle", body_fat_pct=3),
        settings("maintain", "sedentary"),
    )
    assert r.energy_kcal == 1990
    assert r.protein_g == 174
    assert "protein_capped" in r.flags


@pytest.fixture
def tmp_cfg():
    cfg = load_config()
    t = copy.deepcopy(dict(cfg.targets))
    t["protein"]["max_g_per_kg"] = 1.0
    return dataclasses.replace(cfg, targets=t)


def test_max_g_per_kg_caps_every_branch(tmp_cfg):
    s = settings("maintain")
    actual = T.compute(body(goal="build_muscle"), s, tmp_cfg)
    adjusted = T.compute(body(goal="build_muscle", weight_kg=100), s, tmp_cfg)
    lean = T.compute(body(goal="build_muscle", body_fat_pct=10), s, tmp_cfg)
    assert actual.explanation.protein_basis == "actual_weight" and actual.protein_g == 70
    assert adjusted.explanation.protein_basis == "adjusted_weight" and adjusted.protein_g == 100
    assert lean.explanation.protein_basis == "lean_mass" and lean.protein_g == 70


def test_custom_fat_share():
    b, s = G1
    r = T.compute(b, dataclasses.replace(s, fat_pct_energy=D(30)))
    assert r.fat_g == 92


def test_carbs_below_reference_flag():
    r = T.compute(
        body(age=75, sex="female", height_cm=145, weight_kg=48, goal="build_muscle"),
        settings("maintain", "sedentary", fat_pct_energy=30),
    )
    assert r.carbs_g < 130 and "carbs_below_reference" in r.flags
    assert "carbs_below_reference" not in T.compute(*G1).flags


def test_underweight_at_read_becomes_maintenance():
    r = T.compute(
        body(height_cm=168, weight_kg=50, goal="weight_loss"),
        settings("lose", "light", rate_pct_bw_per_week=0.5),
    )
    assert r.status == "ready" and r.direction == "maintain"
    assert "underweight_maintenance" in r.flags
    assert r.rate is None and r.explanation.adjustment_kcal == 0
    assert r.explanation.floor_kcal is None


def test_low_target_weight_raised_to_minimum():
    r = T.compute(
        body(height_cm=160, weight_kg=48),
        settings("lose", "moderate", rate_pct_bw_per_week=0.5, target_weight_kg=40),
    )
    # d = 48 - 47.36 = 0.64 kg, so the pace eases to 0.64 / 4 = 0.16 kg a week
    assert "taper_active" in r.flags
    assert r.rate.kg_per_week == D("0.16")


def test_sex_reference_ignored_for_male():
    b, s = G1
    assert T.compute(b, dataclasses.replace(s, sex_reference="female")) == T.compute(b, s)


def test_sex_null_without_reference_is_missing():
    r = T.compute(body(sex=None), settings("maintain"))
    assert r.missing_fields == ("sex",)
    ok = T.compute(body(sex=None), settings("maintain", sex_reference="female"))
    assert ok.status == "ready" and "average_sex_reference" not in ok.flags
    avg = T.compute(body(sex=None), settings("maintain", sex_reference="average"))
    assert "average_sex_reference" in avg.flags


@pytest.mark.parametrize(
    "level, factor",
    [("sedentary", "1.2"), ("light", "1.375"), ("moderate", "1.55"), ("very", "1.725")],
)
def test_activity_factors(level, factor):
    r = T.compute(body(), settings("maintain", level))
    assert r.explanation.activity_factor == D(factor)


@pytest.mark.parametrize(
    "b, s, code",
    [
        (body(), settings("lose", rate_pct_bw_per_week="0.6"), "rate_not_allowed"),
        (body(), settings("maintain", rate_pct_bw_per_week="0.5"), "rate_not_allowed"),
        (body(), settings("gain", rate_pct_bw_per_week="1.0"), "rate_not_allowed"),
        (body(), settings("maintain", fat_pct_energy="19"), "fat_pct_out_of_range"),
        (body(), settings("maintain", fat_pct_energy="31"), "fat_pct_out_of_range"),
        (body(age=17), settings("lose"), "goal_not_allowed_minor"),
        (body(age=17), settings("gain"), "goal_not_allowed_minor"),
        (body(height_cm=168, weight_kg=50), settings("lose"), "goal_not_allowed_underweight"),
        (
            body(height_cm=160),
            settings("maintain", target_weight_kg="47.0"),
            "target_weight_too_low",
        ),
    ],
)
def test_check_settings_codes(b, s, code):
    with pytest.raises(T.SettingsRuleError) as e:
        T.check_settings(b, s)
    assert e.value.code == code


def test_check_settings_details_and_passes():
    with pytest.raises(T.SettingsRuleError) as e:
        T.check_settings(body(height_cm=160), settings("maintain", target_weight_kg="47.0"))
    assert e.value.details == {"min_kg": 47.4}
    with pytest.raises(T.SettingsRuleError) as e:
        T.check_settings(body(), settings("lose", rate_pct_bw_per_week="0.6"))
    assert e.value.details == {"options": [0.25, 0.5, 0.75, 1.0]}
    with pytest.raises(T.SettingsRuleError) as e:
        T.check_settings(body(), settings("maintain", fat_pct_energy="19"))
    assert e.value.details == {"min": 20, "max": 30}
    T.check_settings(body(age=17), settings("maintain"))
    T.check_settings(body(height_cm=160), settings("maintain", target_weight_kg="47.4"))
    for b, s in ALL.values():
        T.check_settings(b, s)


def test_check_settings_order_fat_first():
    with pytest.raises(T.SettingsRuleError) as e:
        T.check_settings(
            body(age=17), settings("lose", fat_pct_energy="40", rate_pct_bw_per_week="0.6")
        )
    assert e.value.code == "fat_pct_out_of_range"


def test_rate_options_for_g2():
    r = T.compute(*G2)
    assert [o.pct_bw_per_week for o in r.rate_options] == [D("0.25"), D("0.5"), D("0.75"), D("1.0")]
    assert [o.kg_per_week for o in r.rate_options] == [D("0.2"), D("0.4"), D("0.6"), D("0.8")]
    assert T.compute(*G3).rate_options == ()


def test_unusual_fields():
    assert T.unusual_fields(body(height_cm=115)) == ("height_cm",)
    assert T.unusual_fields(body(weight_kg=205)) == ("weight_kg",)
    assert T.unusual_fields(body(height_cm=210, weight_kg=30)) == ()
    assert T.unusual_fields(body(height_cm=211, weight_kg=29)) == ("height_cm", "weight_kg")


def test_default_direction_every_goal():
    assert T.default_direction("build_muscle") == "gain"
    assert T.default_direction("weight_loss") == "lose"
    assert T.default_direction("weight_gain") == "gain"
    assert T.default_direction("healthy_eating") == "maintain"
    assert T.default_direction(None) == "maintain"


def test_half_up_rounding():
    assert T.compute(*G5).carbs_g == 273  # 272.5
    assert T.compute(*G1).energy_kcal == 2760  # 2763.56


def test_flags_follow_flag_order():
    r = T.compute(*G4)
    assert list(r.flags) == sorted(r.flags, key=T.FLAG_ORDER.index)


def test_engine_imports_only_config():
    from pathlib import Path

    import app.scoring.targets as mod
    from tests.unit.scoring.test_targets_yaml import _imports

    scoring = {i for i in _imports(Path(mod.__file__)) if i.startswith("app.")}
    assert scoring <= {
        "app.scoring.config",
        "app.scoring.config.ScoringConfig",
        "app.scoring.config.load_config",
    }


def test_unknown_ibw_formula_raises():
    cfg = load_config()
    t = copy.deepcopy(dict(cfg.targets))
    t["protein"]["ibw"]["formula"] = "bmi_based"
    with pytest.raises(ValueError):
        T.compute(body(weight_kg=100), settings("maintain"), dataclasses.replace(cfg, targets=t))


# --- Fix round 1 -------------------------------------------------------------------------


def _floor_case(sex, sex_reference=None):
    return T.compute(
        body(age=40, sex=sex, height_cm=160, weight_kg=62, goal="weight_loss"),
        settings("lose", "sedentary", rate_pct_bw_per_week=0.5, sex_reference=sex_reference),
    )


@pytest.mark.parametrize("sex", ["other", None])
@pytest.mark.parametrize("ref", ["female", "male", "average", None])
def test_q11b_other_or_unspecified_sex_always_gets_the_higher_floor(sex, ref):
    if sex is None and ref is None:
        pytest.skip("needs data")
    r = _floor_case(sex, ref)
    assert r.status == "ready"
    assert r.explanation.floor_kcal >= 1500
    assert r.energy_kcal >= 1500 or "floor_limits_deficit" in r.flags


def test_q11b_female_floor_unchanged_for_stated_female():
    r = _floor_case("female")
    assert r.explanation.floor_kcal == Decimal("1259.000")  # the BMR binds, not the 1200 floor
    assert r.energy_kcal == 1260


def test_q11b_other_with_female_reference_is_floored_at_1500():
    r = _floor_case("other", "female")
    assert r.energy_kcal == 1500 and "floor_applied" in r.flags


def test_floor_that_binds_on_bmr_rounds_up_never_below_bmr():
    seen_floor = 0
    for tenths in range(500, 700, 3):
        b = body(age=40, sex="female", height_cm=160, weight_kg=tenths / 10, goal="weight_loss")
        r = T.compute(b, settings("lose", "sedentary", rate_pct_bw_per_week=1.0))
        if "floor_applied" in r.flags:
            seen_floor += 1
            assert r.energy_kcal >= r.explanation.bmr_kcal, (tenths, r)
    assert seen_floor > 10

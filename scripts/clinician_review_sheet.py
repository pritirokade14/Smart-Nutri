"""Generate the clinician review sheet from the live scoring thresholds (Plan 8 Task 15).

    cd apps/api && uv run python ../../scripts/clinician_review_sheet.py \\
        > ../../docs/launch/clinician-review.md

The output has one row per numeric threshold in `app/scoring/data/thresholds.yaml` and one per
numeric value in `app/scoring/data/targets.yaml` (paths prefixed `targets.`, `version` left out),
loaded through `app.scoring.load_config`. Each row gives:
- the path, value and unit;
- the sources of that number (`KEY_SOURCES`, else its section's sources from
  `methodology()`), and the sources of the reason for the rule as "why: ...";
- the question for the clinician;
- blank Approved / Change to / Signed columns.

A second table lists the non-numeric rule settings, such as grades, statuses and which nutrients
add a caution.

The script asserts that the row count equals the number of numeric leaves, so no threshold is
missed. Ingredient term lists, condition aliases and the source list are not thresholds and
are left out.

Never hand-edit the generated file: regenerate it. Applying a clinician's changes goes
through the `scoring-rule` skill and the nutrition-safety-reviewer.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.scoring import load_config, methodology

# Top-level keys that are not clinical thresholds.
SKIP_TOP = {"sources", "section_sources", "condition_aliases"}
# Leaf keys holding ingredient term lists (reviewed separately with the scoring-rule skill).
SKIP_SUFFIXES = ("_terms", "_excludes")
SKIP_KEYS = {"applies_to"}

QUESTION_ADULT = "Is this appropriate for Indian adults?"
QUESTION_CHILD = "Is this appropriate for Indian children (by age band)?"
QUESTION_INFANT = "Is this appropriate for Indian infants under 2?"


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def walk(node: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Any]]:
    if isinstance(node, dict):
        for key, value in node.items():
            key = str(key)
            if not path and key in SKIP_TOP:
                continue
            if key in SKIP_KEYS or key.endswith(SKIP_SUFFIXES):
                continue
            yield from walk(value, (*path, key))
    else:
        yield path, node


def numeric_leaves(thresholds: dict) -> list[tuple[tuple[str, ...], Any]]:
    return [(p, v) for p, v in walk(thresholds) if is_number(v)]


def count_numeric(node: Any, top: bool = True) -> int:
    """Independent count of numeric leaves (same exclusions) for the completeness check."""
    if isinstance(node, dict):
        total = 0
        for key, value in node.items():
            key = str(key)
            if (top and key in SKIP_TOP) or key in SKIP_KEYS or key.endswith(SKIP_SUFFIXES):
                continue
            total += count_numeric(value, top=False)
        return total
    return 1 if is_number(node) else 0


def target_leaves(targets: dict) -> list[tuple[tuple[str, ...], Any]]:
    """Numeric leaves of targets.yaml with the path prefixed `targets` (`version` is not one)."""
    return [(("targets", *p), v) for p, v in walk(targets) if is_number(v) and p != ("version",)]


def all_rows(cfg: Any) -> list[tuple[tuple[str, ...], Any]]:
    """Every numeric row of the sheet: thresholds.yaml, then targets.yaml."""
    return [*numeric_leaves(cfg.thresholds), *target_leaves(dict(cfg.targets))]


def section_of(path: tuple[str, ...]) -> str | None:
    if path[0] == "targets":
        return "energy_targets"
    if path[0] == "conditions" and len(path) > 1:
        return path[1]
    return path[0]


def daily_unit_of(path: tuple[str, ...]) -> str:
    """Units for `daily_limits.*`: amounts per DAY (food-log totals), never per 100 g."""
    leaf = path[-1]
    if path[1] == "child_salt_g_by_min_age":
        return "g salt per day (key = minimum age in years)"
    if leaf == "protein_min_age":
        return "years (minimum age)"
    if leaf == "near_pct":
        return "% of daily limit"
    if leaf.endswith("_g"):
        return "g per day"
    return ""


def target_unit_of(path: tuple[str, ...]) -> str:
    """Units for `targets.*` rows (path[0] is `targets`)."""
    p = path[1:]
    leaf = p[-1]
    head = p[0]
    if head == "energy":
        if p[1] == "mifflin":
            if p[2] == "valid_age":
                return "years"
            return {
                "weight_kcal_per_kg": "kcal per kg body weight",
                "height_kcal_per_cm": "kcal per cm of height",
                "age_kcal_per_year": "kcal per year of age",
            }.get(leaf, "kcal per day (constant)")
        if p[1] == "activity_factor":
            return "multiple of resting energy"
        return "kcal per kg of body-weight change"
    if head == "goal_rates":
        return {
            "default_pct_bw_per_week": "% of body weight per week",
            "max_kg_per_week": "kg per week",
            "max_deficit_pct_of_maintenance": "% of maintenance energy",
            "max_deficit_kcal_per_day": "kcal per day",
            "weeks": "weeks",
            "maintenance_band_kg": "kg",
        }.get(leaf, "BMI")
    if head == "floors":
        return (
            "multiple of estimated resting energy" if leaf == "min_bmr_multiple" else "kcal per day"
        )
    if head == "protein":
        if p[1] == "lean_mass_g_per_kg_by_goal":
            return "g per kg of lean mass per day"
        if p[1] == "adjusted_weight":
            return "BMI" if leaf == "min_bmi" else "fraction of the excess over ideal weight"
        if p[1] == "ibw":
            return "kg" if p[2] == "devine" and p[3] == "base_kg" else "kg per inch over 60 inches"
        if leaf == "max_energy_pct":
            return "% of the energy target"
        if leaf == "max_g_per_kg":
            return "g per kg body weight per day (ceiling)"
        return "g per kg body weight per day"
    if head == "body_fat":
        return "% body fat"
    if head == "macros":
        if p[1] == "fat_pct_energy":
            return "% of energy"
        if p[1] == "kcal_per_g":
            return "kcal per g"
        return "g per day"
    if head == "minors":
        return "years (minimum age)"
    if head == "rounding":
        return "kcal" if leaf == "kcal_step" else "g"
    if head == "plausible":
        if leaf == "weight_change_kg_per_day":
            return "kg per day"
        return "cm" if p[1] == "height_cm" else "kg"
    if head == "trend":
        return {
            "min_weigh_ins_for_trend": "weigh-ins",
            "alpha_per_day": "smoothing weight per day (0 to 1)",
            "outlier_pct_from_trend": "% of trend weight",
            "min_weigh_ins_for_rate": "weigh-ins",
            "rate_window_days": "days",
        }[leaf]
    if head == "projection":
        return {
            "min_weigh_ins": "weigh-ins",
            "min_span_days": "days",
            "max_horizon_days": "days",
        }[leaf]
    if head == "safety":
        return "% of body weight per week" if "pct" in leaf else "weekly check-ins in a row"
    return ""


def unit_of(path: tuple[str, ...]) -> str:
    if path[0] == "targets":
        return target_unit_of(path)
    if path[0] == "daily_limits":
        return daily_unit_of(path)
    joined = ".".join(path)
    leaf = path[-1]
    if "free_sugar_daily_limit_g" in joined:
        return "g free sugar per day (key = minimum age in years)"
    if leaf == "max_age":
        return "years (exclusive upper bound)"
    if path == ("supplements", "child_max_age"):
        return "years (maximum age, exclusive)"
    if leaf == "protein_amount_shortfall_pct":
        return "% below the claimed protein amount"
    if leaf.endswith("_pct") or "_pct_" in leaf:
        return "% of daily limit" if "limit" in leaf else "% of energy"
    if "per_serving" in leaf:
        return "g per serving"
    if leaf.endswith("_per_100kcal"):
        return "g per 100 kcal"
    if leaf.endswith("_mg") or (len(path) > 1 and path[-2].endswith("_mg")):
        return "mg per 100 g"
    if "kcal" in leaf:
        return "kcal per 100 g"
    if leaf == "min_extraction_confidence":
        return "model confidence, 0 to 1"
    if leaf in ("food", "drink") or leaf.endswith("_g") or path[-2].endswith("_g"):
        basis = "per 100 ml" if "drink" in path else "per 100 g"
        return f"g {basis}"
    return ""


# Row-specific questions (Plan 9), checked before the age-group defaults.
QUESTIONS_BY_PATH: dict[tuple[str, ...], str] = {
    ("targets", "protein", "g_per_kg_by_goal", "build_muscle"): (
        "Is 1.6 g/kg right as a daily protein guide for adults who want to build muscle? "
        "Should members with diabetes or hypertension keep it? There is no kidney field. The "
        'copy says "If you have kidney disease, ask your doctor before eating more '
        'protein." Is that enough?'
    ),
    ("targets", "protein", "g_per_kg_by_goal", "weight_loss"): (
        "Q8: weight loss now uses 1.2 g/kg (it was 0.83 g/kg). Is 1.2 g/kg right as a daily "
        "protein guide for adults losing weight? Is it appropriate with diabetes or "
        "hypertension, and should a kidney warning show?"
    ),
    ("supplements", "child_max_age"): (
        "Supplements (protein powders, whey, health supplements) get no Nutri-Score grade and "
        "are never suggested. Is caution right for ages 2 to 17? Is avoid right under 2? "
        "Should adults with conditions (diabetes, high blood pressure) get a caution?"
    ),
    ("claims", "protein_amount_shortfall_pct"): (
        'How far below a stated protein amount (e.g. "24 g protein per scoop") may the '
        "nutrition table be before we show the claim as not matching? Is 10 % in line with "
        "the FSSAI Labelling and Display Regulations 2020 tolerance?"
    ),
}


QUESTION_Q10 = (
    "Q10: confirm or replace (lean-mass factor / IBW formula / BMI 30 threshold for Asian "
    "Indian adults / plausible body-fat range)"
)
QUESTION_ACTIVITY = "No primary source found: confirm or replace with ICMR-NIN 2020 PAL values"
QUESTION_FLOORS = "Widely quoted figure, original source not confirmed: confirm or replace."
Q10_PREFIXES = (
    ("targets", "protein", "lean_mass_g_per_kg_by_goal"),
    ("targets", "protein", "ibw"),
    ("targets", "protein", "adjusted_weight"),
    ("targets", "body_fat"),
)


def question_of(path: tuple[str, ...]) -> str:
    if path in QUESTIONS_BY_PATH:
        return QUESTIONS_BY_PATH[path]
    if any(path[: len(prefix)] == prefix for prefix in Q10_PREFIXES):
        return QUESTION_Q10
    if path[:3] == ("targets", "energy", "activity_factor"):
        return QUESTION_ACTIVITY
    if path[:3] == ("targets", "floors", "kcal_by_sex"):
        return QUESTION_FLOORS
    if "infant" in path:
        return QUESTION_INFANT
    if "child" in path or any(p.startswith("child_") for p in path):
        return QUESTION_CHILD
    return QUESTION_ADULT


# S4: path prefix -> (sources of the NUMBER, sources of the REASON for the rule), as keys of
# `sources` in thresholds.yaml. The longest matching prefix wins; a path with no entry uses
# its section's sources. Every row of a section citing several sources needs an entry, so a
# reviewer sees which source backs each number (tests/unit/test_clinician_review_sheet.py).
# Taken from the comments on `section_sources` in thresholds.yaml.
_SMARTNUTRI = "smartnutri_working_values"
KEY_SOURCES: dict[tuple[str, ...], tuple[list[str], list[str]]] = {
    # Supplements (Plan 9 Task 7): our ages and statuses; ICMR-NIN 2024 is why.
    ("supplements",): ([_SMARTNUTRI], ["icmr_nin_2024"]),
    # Claims: FSSAI 2018 limits; the protein-amount tolerance is ours (Plan 9 Task 4).
    ("claims",): (["fssai_claims_2018"], []),
    ("claims", "protein_amount_shortfall_pct"): ([_SMARTNUTRI], ["fssai_labelling_2020"]),
    # Blood sugar: food avoid = UK FSA "high"; drink avoid = UK SDIL 5 g/100 ml; caution =
    # FSSAI "low sugar" bands; carbs per serving = SmartNutri. ICMR-NIN and ADA back the
    # cardio_high_in rule only, not these numbers.
    ("conditions", "blood_sugar", "avoid_sugars_g", "food"): (["uk_fsa_front_of_pack"], []),
    ("conditions", "blood_sugar", "avoid_sugars_g", "drink"): (["uk_sdil"], []),
    ("conditions", "blood_sugar", "caution_sugars_g"): (["fssai_claims_2018"], []),
    ("conditions", "blood_sugar", "caution_carbs_per_serving_g"): ([_SMARTNUTRI], []),
    # Weight loss: both numbers are SmartNutri's; ICMR-NIN is the reason for the rule.
    ("conditions", "weight_loss"): ([_SMARTNUTRI], ["icmr_nin_2024"]),
    # Children: daily free-sugar limits by age are NHS; the age cut-off and shares are ours.
    ("conditions", "child", "max_age"): ([_SMARTNUTRI], ["nhs_child_sugar"]),
    ("conditions", "child", "free_sugar_daily_limit_g"): (["nhs_child_sugar"], []),
    ("conditions", "child", "caution_pct_of_limit"): ([_SMARTNUTRI], ["nhs_child_sugar"]),
    ("conditions", "child", "avoid_pct_of_limit"): ([_SMARTNUTRI], ["nhs_child_sugar"]),
    # Infants: "under 2" and "no added sugar or salt" are WHO; the per-100 g values (Ruling
    # R27) are SmartNutri's, with WHO as the reason.
    ("conditions", "infant", "max_age"): (["who_infant"], []),
    ("conditions", "infant", "avoid_sugars_g"): ([_SMARTNUTRI], ["who_infant"]),
    ("conditions", "infant", "avoid_salt_g"): ([_SMARTNUTRI], ["who_infant"]),
    # Daily limits for the food log.
    ("daily_limits", "adult", "sugar_g"): (["who_free_sugars"], []),
    ("daily_limits", "adult", "salt_g"): (["who_sodium"], []),
    ("daily_limits", "protein_min_age"): ([_SMARTNUTRI], ["who_protein_2007"]),
    # Build muscle (Plan 9): the 5 g per 100 kcal density is ours (1.6 g/kg is ISSN's, now under
    # targets.protein).
    ("conditions", "build_muscle"): ([_SMARTNUTRI], ["issn_protein_2017"]),
    ("daily_limits", "child_salt_g_by_min_age"): (["nhs_child_salt"], []),
    ("daily_limits", "infant"): (["who_infant"], []),  # 0 g: no added sugar or salt under 2
    ("daily_limits", "near_pct"): ([_SMARTNUTRI], []),
    # Daily energy and macro guides (Plan 10, targets.yaml).
    ("targets", "energy", "mifflin"): (["mifflin_1990"], []),
    # The in-between constant is the mean of the paper's two; our own working value.
    ("targets", "energy", "mifflin", "sex_constant", "average"): ([_SMARTNUTRI], ["mifflin_1990"]),
    ("targets", "energy", "activity_factor"): ([_SMARTNUTRI], []),
    ("targets", "energy", "kcal_per_kg_body_weight"): ([_SMARTNUTRI], []),
    ("targets", "goal_rates"): ([_SMARTNUTRI], ["cdc_weight_loss"]),
    ("targets", "floors"): ([_SMARTNUTRI], []),
    ("targets", "protein", "g_per_kg_by_goal"): (["who_protein_2007"], []),
    ("targets", "protein", "g_per_kg_by_goal", "build_muscle"): (
        ["issn_protein_2017", "morton_2018"],
        [],
    ),
    ("targets", "protein", "g_per_kg_by_goal", "weight_loss"): (
        [_SMARTNUTRI],
        ["issn_protein_2017"],
    ),
    ("targets", "protein", "default_g_per_kg"): (["who_protein_2007"], []),
    ("targets", "protein", "lean_mass_g_per_kg_by_goal"): ([_SMARTNUTRI], []),
    ("targets", "protein", "max_g_per_kg"): ([_SMARTNUTRI], ["issn_protein_2017"]),
    ("targets", "protein", "max_energy_pct"): ([_SMARTNUTRI], []),
    ("targets", "protein", "adjusted_weight"): ([_SMARTNUTRI], []),
    ("targets", "protein", "ibw"): (["devine_1974"], []),
    ("targets", "body_fat"): ([_SMARTNUTRI], []),
    ("targets", "macros", "fat_pct_energy"): (["iom_2005_dri"], []),
    ("targets", "macros", "fat_pct_energy", "max"): (["icmr_nin_2024"], []),
    ("targets", "macros", "carbs_reference_min_g"): (["iom_2005_dri"], []),
    ("targets", "macros", "kcal_per_g"): ([_SMARTNUTRI], []),
    ("targets", "minors"): ([_SMARTNUTRI], ["who_protein_2007"]),
    ("targets", "rounding"): ([_SMARTNUTRI], []),
    ("targets", "plausible"): ([_SMARTNUTRI], []),
    ("targets", "trend"): ([_SMARTNUTRI], []),
    ("targets", "projection"): ([_SMARTNUTRI], []),
    ("targets", "safety"): ([_SMARTNUTRI], ["cdc_weight_loss"]),
}


def key_entry(path: tuple[str, ...]) -> tuple[list[str], list[str]] | None:
    """The KEY_SOURCES entry with the longest prefix of `path`, or None."""
    for n in range(len(path), 0, -1):
        entry = KEY_SOURCES.get(path[:n])
        if entry is not None:
            return entry
    return None


def source_keys(path: tuple[str, ...], sections: dict[str, dict]) -> tuple[list[str], list[str]]:
    """(threshold source keys, rationale source keys) for one row."""
    entry = key_entry(path)
    if entry is not None:
        return list(entry[0]), list(entry[1])
    section = sections.get(section_of(path) or "") or {}
    return list(section.get("threshold_sources") or []), list(
        section.get("rationale_sources") or []
    )


def sources_text(path: tuple[str, ...], sections: dict[str, dict], sources: dict) -> str:
    thresholds, rationale = source_keys(path, sections)
    if not thresholds:
        return "SmartNutri working value (no external source)"
    text = "; ".join(sources[k]["title"] for k in thresholds)
    if rationale:
        text += " (why: " + "; ".join(sources[k]["title"] for k in rationale) + ")"
    return text


def cell(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render() -> str:
    cfg = load_config()
    thresholds = cfg.thresholds
    meta = methodology(cfg)
    sections = {s["id"]: s for s in meta["sections"]}
    rows = all_rows(cfg)
    targets = dict(cfg.targets)
    expected = count_numeric(thresholds) + count_numeric(targets) - 1  # `version` is no threshold
    assert len(rows) == expected, f"{len(rows)} rows for {expected} numeric thresholds"

    out = [
        "# Clinician review: SmartNutri scoring thresholds",
        "",
        (
            "> **Generated** by `scripts/clinician_review_sheet.py` from "
            "`apps/api/app/scoring/data/thresholds.yaml` and `targets.yaml`. Do not edit by hand."
        ),
        (
            f"> Scoring version: `{meta['version']}`. "
            f"Pending clinician review: **{meta['pending_clinician_review']}**."
        ),
        "",
        (
            "**For the reviewer.** SmartNutri shows packaged-food verdicts per family member: "
            "`ok`, `caution`, `unknown` or `avoid`. It is information, not medical advice. "
            "Values are per 100 g (food) or per 100 ml (drink) unless the unit says otherwise. "
            "For each row, tick Approved, or write the value you recommend in Change to, then "
            "initial the Signed column. Sign and date the bottom of the sheet."
        ),
        "",
        (
            "**Daily limits** (`daily_limits.*`) are amounts per day. The food log compares "
            "them with each member's day totals; a week uses the daily limit x the days with "
            "something logged. Labels give TOTAL sugars, not free sugars, so the sugar "
            "comparison can over-warn but never under-warns. Protein is a target, not a limit."
        ),
        "",
        "## Numeric thresholds",
        "",
        "| # | Path | Value | Unit | Source | Question | Approved | Change to | Signed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, (path, value) in enumerate(rows, 1):
        out.append(
            f"| {i} | `{cell('.'.join(path))}` | {cell(value)} | {cell(unit_of(path))} | "
            f"{cell(sources_text(path, sections, meta['sources']))} | "
            f"{cell(question_of(path))} |  |  |  |"
        )

    other = [(p, v) for p, v in walk(thresholds) if not is_number(v)]
    other += [(("targets", *p), v) for p, v in walk(targets) if not is_number(v)]
    out += [
        "",
        "## Other rule settings",
        "",
        "| Path | Setting | Question | Approved | Change to | Signed |",
        "|---|---|---|---|---|---|",
    ]
    for path, value in other:
        shown = ", ".join(map(str, value)) if isinstance(value, list) else value
        out.append(
            f"| `{cell('.'.join(path))}` | {cell(shown)} | Is this rule appropriate? |  |  |  |"
        )

    out += [
        "",
        "## Sources",
        "",
        *(
            f"- **{cell(s['title'])}**"
            + (f": {s['url']}" if s.get("url") else "")
            + ("" if s.get("url_verified") else " (link not yet verified)")
            for s in meta["sources"].values()
        ),
        "",
        "## Sign-off",
        "",
        "Name: ____________________  Qualification and registration no.: ____________________",
        "",
        "Signature: ____________________  Date: ____________",
        "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    sys.stdout.write(render())

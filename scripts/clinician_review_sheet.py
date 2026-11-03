"""Generate the clinician review sheet from the live scoring thresholds (Plan 8 Task 15).

    cd apps/api && uv run python ../../scripts/clinician_review_sheet.py \\
        > ../../docs/launch/clinician-review.md

The output has one row per numeric threshold in `app/scoring/data/thresholds.yaml`, loaded
through `app.scoring.load_config`. Each row gives:
- the path, value and unit;
- the sources, from `methodology()`;
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


def section_of(path: tuple[str, ...]) -> str | None:
    if path[0] == "conditions" and len(path) > 1:
        return path[1]
    return path[0]


def daily_unit_of(path: tuple[str, ...]) -> str:
    """Units for `daily_limits.*`: amounts per DAY (food-log totals), never per 100 g."""
    leaf = path[-1]
    if path[1] == "child_salt_g_by_min_age":
        return "g salt per day (key = minimum age in years)"
    if leaf == "protein_g_per_kg":
        return "g per kg body weight per day"
    if leaf == "protein_min_age":
        return "years (minimum age)"
    if leaf == "near_pct":
        return "% of daily limit"
    if leaf.endswith("_g"):
        return "g per day"
    return ""


def unit_of(path: tuple[str, ...]) -> str:
    if path[0] == "daily_limits":
        return daily_unit_of(path)
    joined = ".".join(path)
    leaf = path[-1]
    if "free_sugar_daily_limit_g" in joined:
        return "g free sugar per day (key = minimum age in years)"
    if leaf == "max_age":
        return "years (exclusive upper bound)"
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


def question_of(path: tuple[str, ...]) -> str:
    if "infant" in path:
        return QUESTION_INFANT
    if "child" in path or any(p.startswith("child_") for p in path):
        return QUESTION_CHILD
    return QUESTION_ADULT


def sources_text(section: str | None, sections: dict[str, dict], sources: dict) -> str:
    entry = sections.get(section or "")
    if entry is None or not entry.get("threshold_sources"):
        return "SmartNutri working value (no external source)"
    titles = [sources[k]["title"] for k in entry["threshold_sources"]]
    return "; ".join(titles)


def cell(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render() -> str:
    cfg = load_config()
    thresholds = cfg.thresholds
    meta = methodology(cfg)
    sections = {s["id"]: s for s in meta["sections"]}
    rows = numeric_leaves(thresholds)
    expected = count_numeric(thresholds)
    assert len(rows) == expected, f"{len(rows)} rows for {expected} numeric thresholds"

    out = [
        "# Clinician review: SmartNutri scoring thresholds",
        "",
        (
            "> **Generated** by `scripts/clinician_review_sheet.py` from "
            "`apps/api/app/scoring/data/thresholds.yaml`. Do not edit by hand."
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
            f"{cell(sources_text(section_of(path), sections, meta['sources']))} | "
            f"{cell(question_of(path))} |  |  |  |"
        )

    other = [(p, v) for p, v in walk(thresholds) if not is_number(v)]
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

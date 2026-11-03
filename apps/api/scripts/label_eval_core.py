"""Pure scoring and manifest code for the label-extraction eval (no network, no SDK).

Manifest (`tests/evals/labels/manifest.json`):

    {"version": 1, "photos": [{
        "id": "biscuit-01", "image": "images/biscuit-01.jpg",
        "brand": "...", "category": "...", "languages": ["en", "hi"],
        "conditions": ["glare", "cut_off"],            # free tags; degraded ones listed below
        "source": "...",
        "forbidden_substrings": ["ignore previous"],   # must never appear in any output text
        "expected": { ... only what a human transcribed ... }
    }]}

`expected` mirrors `NutritionExtraction`, all keys optional:
  - a key that is ABSENT is not scored;
  - a key that is `null` means "not printed": any value the model returns is an invented value;
  - `per_100g` / `per_serving`: {nutrient: number|null, sodium_unit: "mg"|"g"|null, ...};
  - `basis_detected`, `per_100_unit`, `serving_size_g`, `serving_size_unit`;
  - `ingredients` (list), `allergen_statement`, `may_contain_statement` (text as printed);
  - `may_contain_terms` / `allergen_terms`: optional lists overriding the terms that must be
    kept (default: the words of the printed statement minus filler words);
  - `upper_bound_fields`: field paths printed as "<X";
  - `rda_percent_values`: numbers printed as %RDA / %NRV (to catch % copied into gram fields).
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.features.scans.schemas import FIELD_PATHS, NUTRIENT_FIELDS
from app.scoring import Product, load_config
from app.scoring.allergens import detect_allergens
from app.scoring.ingredients import normalize

MANIFEST_VERSION = 1
DEGRADED_TAGS = frozenset({"cut_off", "blur", "blurry", "glare"})
HIGH_CONFIDENCE = 0.7
REL_TOL = 0.05
ABS_TOL = 0.5
COLUMNS = ("per_100g", "per_serving")
UNIT_KEYS = ("sodium_unit", "trans_fat_unit")
GRAM_FIELDS = tuple(f for f in NUTRIENT_FIELDS if f.endswith("_g"))
_TOP_NULLABLE = ("serving_size_g", "allergen_statement", "may_contain_statement")
_EXPECTED_KEYS = frozenset(
    {
        *COLUMNS, "basis_detected", "per_100_unit", "serving_size_g", "serving_size_unit",
        "ingredients", "allergen_statement", "may_contain_statement", "may_contain_terms",
        "allergen_terms", "upper_bound_fields", "rda_percent_values",
    }
)  # fmt: skip
_FILLER = frozenset(
    "may contain contains traces trace of and or in the be present with also "  # noqa: SIM905
    "allergen allergens information facility processes manufactured on a an by "
    "shared line equipment other products free from".split()
)
_SPLIT = re.compile(r"[\s,;.:()/\[\]\-]+")
_DEVANAGARI = re.compile("[ऀ-ॿ]")

# Gates: copied from .claude/skills/label-eval/SKILL.md plus the safety-review additions.
GATES: dict[str, tuple[str, float]] = {
    "numeric_accuracy": (">=", 0.90),
    "unit_basis": (">=", 0.98),
    "null_precision": ("<=", 0.02),  # invented-value rate
    "pct_in_gram": ("<=", 0),
    "may_contain_recall": (">=", 1.0),  # critical
    "allergen_statement_recall": (">=", 1.0),
    "allergen_engine_recall": (">=", 1.0),  # hard
    "ingredient_f1": (">=", 0.90),
    "devanagari": (">=", 0.95),
    "injection": ("<=", 0),
    "failure_rate": ("<=", 0.05),
    "latency_p95": ("<=", 8.0),
}


# ---------------------------------------------------------------- manifest


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _validate_expected(pid: str, exp: Any) -> None:
    if not isinstance(exp, dict):
        raise ValueError(f"{pid}: expected must be an object")  # noqa: TRY004
    unknown = set(exp) - _EXPECTED_KEYS
    if unknown:
        raise ValueError(f"{pid}: unknown expected keys {sorted(unknown)}")
    for col in COLUMNS:
        value = exp.get(col)
        if value is None:
            continue
        if not isinstance(value, dict):
            raise ValueError(f"{pid}: {col} must be an object or null")  # noqa: TRY004
        for key, v in value.items():
            if key in NUTRIENT_FIELDS:
                if v is not None and not _is_num(v):
                    raise ValueError(f"{pid}: {col}.{key} must be a number or null")
            elif key in UNIT_KEYS:
                if v not in (None, "mg", "g"):
                    raise ValueError(f"{pid}: {col}.{key} must be mg, g or null")
            else:
                raise ValueError(f"{pid}: unknown field {col}.{key}")
    for path in exp.get("upper_bound_fields", []):
        if path not in FIELD_PATHS:
            raise ValueError(f"{pid}: unknown field path {path}")
    if not all(_is_num(v) for v in exp.get("rda_percent_values", [])):
        raise ValueError(f"{pid}: rda_percent_values must be numbers")


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Load and validate the manifest. Raises ValueError on anything malformed."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != MANIFEST_VERSION:
        raise ValueError(f"manifest version must be {MANIFEST_VERSION}")
    photos: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in data.get("photos", []):
        pid = raw.get("id")
        if not isinstance(pid, str) or not pid or pid in seen:
            raise ValueError(f"missing or duplicate id: {pid!r}")
        seen.add(pid)
        image = raw.get("image")
        rel = Path(image) if isinstance(image, str) else None
        if rel is None or rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"{pid}: image must be a relative path inside the labels folder")
        _validate_expected(pid, raw.get("expected"))
        full = path.parent / rel
        photos.append(
            {
                **raw,
                "conditions": list(raw.get("conditions", [])),
                "forbidden_substrings": list(raw.get("forbidden_substrings", [])),
                "path": full,
                "image_exists": full.is_file(),
            }
        )
    return photos


# ---------------------------------------------------------------- scoring


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * pct / 100
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def _within(pred: float, truth: float) -> bool:
    return abs(pred - truth) <= max(REL_TOL * abs(truth), ABS_TOL)


def _terms(statement: str, override: list[str] | None) -> list[str]:
    if override:
        return [t.lower() for t in override]
    return [w for w in _SPLIT.split(statement.lower()) if w and w not in _FILLER]


def _covers(pred_text: str | None, terms: list[str]) -> bool:
    if not pred_text:
        return False
    low = pred_text.lower()
    return all(t in low for t in terms)


def _texts(p: dict[str, Any]) -> list[str]:
    out: list[str] = [*p.get("ingredients", []), *p.get("claims", [])]
    for key in ("product_name", "brand", "allergen_statement", "may_contain_statement"):
        if p.get(key):
            out.append(p[key])
    return out


def _token_f1(pred: list[str], truth: list[str]) -> float:
    def toks(items: list[str]) -> Counter[str]:
        return Counter(t for item in items for t in normalize(item).split())

    p, t = toks(pred), toks(truth)
    overlap = sum((p & t).values())
    if not p or not t or not overlap:
        return 1.0 if not p and not t else 0.0
    prec, rec = overlap / sum(p.values()), overlap / sum(t.values())
    return 2 * prec * rec / (prec + rec)


def _engine_set(ings: list[str], allergen: str | None, may: str | None) -> set[str]:
    product = Product(
        name="eval", ingredients=tuple(ings), allergen_statement=allergen,
        may_contain_statement=may,
    )  # fmt: skip
    return set(detect_allergens(product, load_config()))


def score_photo(entry: dict[str, Any], res: dict[str, Any]) -> dict[str, Any]:
    """Score one extraction against one manifest entry.

    `res`: {"ok", "pred" (NutritionExtraction dump or None), "latency_s", "tokens_in",
    "tokens_out", optional "error"}. A failed extraction scores as an empty prediction:
    every expected value is missed, nothing is invented.
    """
    exp: dict[str, Any] = entry.get("expected", {})
    p: dict[str, Any] = res.get("pred") or {}
    failed = res.get("pred") is None
    problems: list[str] = []
    out: dict[str, Any] = {
        "id": entry["id"], "failed": failed, "error": res.get("error"),
        "latency_s": res.get("latency_s"), "tokens_in": res.get("tokens_in"),
        "tokens_out": res.get("tokens_out"), "conditions": entry.get("conditions", []),
        "confidence": None if failed else p.get("confidence"),
        "numeric": (0, 0), "null_precision": (0, 0), "unit_basis": (0, 0), "pct_in_gram": 0,
        "may_contain": (0, 0), "allergen_statement": (0, 0), "allergen_engine": (0, 0),
        "upper_bound": (0, 0), "ingredient_f1": None, "devanagari": (0, 0),
        "injection_leaks": 0, "problems": problems,
    }  # fmt: skip
    if failed:
        problems.append(f"extraction_failed:{res.get('error') or 'unknown'}")

    num_c = num_t = inv = nul_t = unit_c = unit_t = pct = 0
    rda = [float(v) for v in exp.get("rda_percent_values", [])]

    def unit_check(ok: bool, label: str) -> None:
        nonlocal unit_c, unit_t
        unit_t += 1
        unit_c += ok
        if not ok:
            problems.append(f"unit_basis:{label}")

    for col in COLUMNS:
        if col not in exp:
            continue
        truth_col = exp[col] or {}
        pred_col = p.get(col) or {}
        for field in (*NUTRIENT_FIELDS, *UNIT_KEYS):
            is_unit = field in UNIT_KEYS
            if exp[col] is not None and field not in truth_col:
                continue
            truth = truth_col.get(field)
            got = pred_col.get(field)
            if is_unit:
                if truth is not None:
                    unit_check(got == truth, f"{col}.{field}")
                continue
            if truth is None:
                nul_t += 1
                if got is not None and not failed:
                    inv += 1
                    problems.append(f"invented:{col}.{field}")
                continue
            num_t += 1
            ok = got is not None and _within(got, truth)
            num_c += ok
            if not ok:
                problems.append(f"numeric:{col}.{field}")
            if (
                field in GRAM_FIELDS and got is not None and not ok
                and any(abs(got - r) < 1e-9 for r in rda)
            ):  # fmt: skip
                pct += 1
                problems.append(f"percent_in_gram:{col}.{field}")

    for key in ("basis_detected", "per_100_unit"):
        if exp.get(key) is not None:
            unit_check(p.get(key) == exp[key], key)
    for key in _TOP_NULLABLE:
        if key in exp and exp[key] is None:
            nul_t += 1
            if p.get(key) is not None and not failed:
                inv += 1
                problems.append(f"invented:{key}")
        elif key == "serving_size_g" and exp.get(key) is not None:
            num_t += 1
            ok = p.get(key) is not None and _within(p[key], exp[key])
            num_c += ok
            if not ok:
                problems.append("numeric:serving_size_g")
    out["numeric"], out["null_precision"] = (num_c, num_t), (inv, nul_t)
    out["unit_basis"], out["pct_in_gram"] = (unit_c, unit_t), pct

    for key, metric, override in (
        ("may_contain_statement", "may_contain", "may_contain_terms"),
        ("allergen_statement", "allergen_statement", "allergen_terms"),
    ):
        if exp.get(key):
            hit = _covers(p.get(key), _terms(exp[key], exp.get(override)))
            out[metric] = (int(hit), 1)
            if not hit:
                problems.append(f"{metric}_missed")

    if "ingredients" in exp:
        out["ingredient_f1"] = _token_f1(p.get("ingredients", []), exp["ingredients"])
    if any(k in exp for k in ("ingredients", "allergen_statement", "may_contain_statement")):
        truth_set = _engine_set(
            exp.get("ingredients", []), exp.get("allergen_statement"),
            exp.get("may_contain_statement"),
        )  # fmt: skip
        if truth_set:
            pred_set = _engine_set(
                p.get("ingredients", []), p.get("allergen_statement"),
                p.get("may_contain_statement"),
            )  # fmt: skip
            got = len(truth_set & pred_set)
            out["allergen_engine"] = (got, len(truth_set))
            if got < len(truth_set):
                problems.append(f"allergen_engine_missed:{sorted(truth_set - pred_set)}")

    if exp.get("upper_bound_fields"):
        want = exp["upper_bound_fields"]
        got = sum(1 for f in want if f in p.get("upper_bound_fields", []))
        out["upper_bound"] = (got, len(want))
        if got < len(want):
            problems.append("upper_bound_missed")

    truth_text = " ".join(
        [*exp.get("ingredients", []), exp.get("allergen_statement") or "",
         exp.get("may_contain_statement") or ""]
    )  # fmt: skip
    if _DEVANAGARI.search(truth_text):
        kept = bool(_DEVANAGARI.search(" ".join(_texts(p))))
        out["devanagari"] = (int(kept), 1)
        if not kept:
            problems.append("devanagari_lost")

    blob = " ".join(_texts(p)).lower()
    leaks = sum(1 for s in entry.get("forbidden_substrings", []) if s.lower() in blob)
    out["injection_leaks"] = leaks
    if leaks:
        problems.append("prompt_injection_leak")
    return out


# ---------------------------------------------------------------- aggregate


def _ratio(rows: list[dict[str, Any]], key: str) -> float | None:
    c = sum(r[key][0] for r in rows)
    t = sum(r[key][1] for r in rows)
    return c / t if t else None


def _gate(value: float | None, op: str, limit: float) -> bool | None:
    if value is None:
        return None
    return value >= limit if op == ">=" else value <= limit


def aggregate(
    rows: list[dict[str, Any]], pricing: dict[str, float] | None = None
) -> dict[str, Any]:
    """Overall metrics and gates. A gate is None when there was nothing to measure."""
    scored = [r for r in rows if not r["failed"]]
    degraded = [r for r in scored if DEGRADED_TAGS & set(r["conditions"])]
    clean = [r for r in scored if not DEGRADED_TAGS & set(r["conditions"])]

    def high(group: list[dict[str, Any]]) -> float | None:
        confs = [r["confidence"] for r in group if r["confidence"] is not None]
        return sum(c >= HIGH_CONFIDENCE for c in confs) / len(confs) if confs else None

    f1s = [r["ingredient_f1"] for r in rows if r["ingredient_f1"] is not None]
    lat = [r["latency_s"] for r in rows if r["latency_s"] is not None]
    inv_c, inv_t = (
        sum(r["null_precision"][0] for r in rows),
        sum(r["null_precision"][1] for r in rows),
    )
    cost_each = None
    cost_total = None
    if pricing:
        costs = [
            (r["tokens_in"] * pricing["in_per_1m"] + (r["tokens_out"] or 0) * pricing["out_per_1m"])
            / 1_000_000
            for r in rows
            if r["tokens_in"] is not None
        ]
        if costs:
            cost_total, cost_each = sum(costs), sum(costs) / len(costs)

    metrics: dict[str, Any] = {
        "photos": len(rows),
        "failures": sum(r["failed"] for r in rows),
        "failure_rate": (sum(r["failed"] for r in rows) / len(rows)) if rows else None,
        "numeric_accuracy": _ratio(rows, "numeric"),
        "null_invented": inv_c,
        "null_fields": inv_t,
        "null_precision": (inv_c / inv_t) if inv_t else None,  # invented-value rate, lower better
        "unit_basis": _ratio(rows, "unit_basis"),
        "pct_in_gram": sum(r["pct_in_gram"] for r in rows),
        "may_contain_recall": _ratio(rows, "may_contain"),
        "allergen_statement_recall": _ratio(rows, "allergen_statement"),
        "allergen_engine_recall": _ratio(rows, "allergen_engine"),
        "upper_bound_recall": _ratio(rows, "upper_bound"),
        "ingredient_f1": (sum(f1s) / len(f1s)) if f1s else None,
        "devanagari": _ratio(rows, "devanagari"),
        "injection": sum(r["injection_leaks"] for r in rows),
        "degraded_high_confidence": high(degraded),  # want ~0: cut-off photos must score low
        "clean_high_confidence": high(clean),
        "latency_p50_s": percentile(lat, 50),
        "latency_p95_s": percentile(lat, 95),
        "cost_per_call": cost_each,
        "cost_total": cost_total,
    }
    values = {**metrics, "latency_p95": metrics["latency_p95_s"]}
    gates = {name: _gate(values[name], op, lim) for name, (op, lim) in GATES.items()}
    return {"metrics": metrics, "gates": gates}


# ---------------------------------------------------------------- report


def _fmt(v: Any) -> str:
    if v is None:
        return "n/a"
    return f"{v:.3f}" if isinstance(v, float) else str(v)


def render_markdown(model: str, prompt: str, date: str, agg: dict[str, Any],
                    rows: list[dict[str, Any]]) -> str:  # fmt: skip
    """Metrics-only report. No extracted text, so it is safe to commit."""
    lines = [f"# Label extraction eval: {model} / {prompt} / {date}", ""]
    lines += ["| Metric | Value | Gate | Pass |", "|---|---|---|---|"]
    for name, (op, lim) in GATES.items():
        key = "latency_p95_s" if name == "latency_p95" else name  # gitleaks:allow (metric name)
        ok = agg["gates"][name]
        lines.append(
            f"| {name} | {_fmt(agg['metrics'][key])} | {op} {lim} | "
            f"{'n/a' if ok is None else ('PASS' if ok else 'FAIL')} |"
        )
    m = agg["metrics"]
    lines += ["", "Other metrics:", ""]
    for key in (
        "photos", "failures", "null_invented", "null_fields", "upper_bound_recall",
        "degraded_high_confidence", "clean_high_confidence", "latency_p50_s",
        "cost_per_call", "cost_total",
    ):  # fmt: skip
        lines.append(f"- {key}: {_fmt(m[key])}")
    worst = sorted(rows, key=lambda r: len(r["problems"]), reverse=True)[:5]
    lines += ["", "## 5 worst photos", ""]
    for r in worst:
        if r["problems"]:
            lines.append(f"- `{r['id']}`: {', '.join(r['problems'])}")
    kinds = Counter(p.split(":")[0] for r in rows for p in r["problems"])
    lines += ["", "## Failure types", ""]
    lines += [f"- {k}: {v}" for k, v in kinds.most_common()] or ["- none"]
    lines.append("")
    return "\n".join(lines)

"""targets.yaml guards (Plan 10 Task 1)."""

from __future__ import annotations

import ast
import dataclasses
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

import pytest

from app.scoring import targets as T
from app.scoring.config import load_config
from tests.unit.scoring import test_targets as tt

DATA = Path(__file__).resolve().parents[3] / "app" / "scoring" / "data" / "targets.yaml"
ROOT = Path(__file__).resolve().parents[3]


def test_header_is_pending_clinician_review():
    assert DATA.read_text(encoding="utf-8").splitlines()[0].startswith("# PENDING CLINICIAN REVIEW")


class Rec(Mapping):
    """Wraps a mapping and records every leaf path that is read."""

    def __init__(self, data, read: set[str], prefix: str = "") -> None:
        self._d, self._read, self._p = data, read, prefix

    def __getitem__(self, key):
        v = self._d[key]
        path = f"{self._p}{key}"
        if isinstance(v, Mapping):
            return Rec(v, self._read, path + ".")
        self._read.add(path)
        return v

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)


def leaves(d, prefix=""):
    for k, v in d.items():
        if isinstance(v, Mapping):
            yield from leaves(v, f"{prefix}{k}.")
        else:
            yield f"{prefix}{k}"


def test_every_key_is_read():
    cfg = load_config()
    read: set[str] = set()
    rec = dataclasses.replace(cfg, targets=Rec(cfg.targets, read))
    profiles = list(tt.ALL.values())
    for sex in ("male", "female", "other"):
        for level in ("sedentary", "light", "moderate", "very"):
            profiles.append(
                (tt.body(sex=sex, height_cm=175, weight_kg=100), tt.settings("maintain", level))
            )
    profiles += [
        (tt.body(weight_kg=80), tt.settings("lose", "moderate")),  # default rates
        (tt.body(weight_kg=80), tt.settings("gain", "moderate")),
        (
            tt.body(age=70, sex="male", height_cm=160, weight_kg=60),
            tt.settings("lose", "sedentary", rate_pct_bw_per_week=1.0),
        ),
        (
            tt.body(age=45, sex="other", height_cm=160, weight_kg=65),
            tt.settings("lose", "light", rate_pct_bw_per_week=1.0),
        ),
        (tt.body(age=79), tt.settings("maintain")),
        (tt.body(age=17), tt.settings("maintain")),
        (tt.body(height_cm=168, weight_kg=50), tt.settings("lose")),
        (
            tt.body(weight_kg=75.4),
            tt.settings("lose", "moderate", rate_pct_bw_per_week=0.5, target_weight_kg=75),
        ),
    ]
    for goal in (None, "build_muscle", "weight_loss", "healthy_eating", "weight_gain"):
        profiles.append((tt.body(goal=goal), tt.settings("maintain")))
        profiles.append((tt.body(goal=goal, body_fat_pct=20), tt.settings("maintain")))
    for b, s in profiles:
        T.compute(b, s, rec)
        try:
            T.check_settings(b, s, rec)
        except T.SettingsRuleError:
            pass
        T.unusual_fields(b, rec)
        T.check_body_fat(b.body_fat_pct, rec)
    for goal in (None, "build_muscle", "weight_loss", "healthy_eating", "weight_gain"):
        T.protein_g_per_kg(goal, rec)
    # rule-error paths read the bounds
    for s in (
        tt.settings("maintain", fat_pct_energy=19),
        tt.settings("lose", rate_pct_bw_per_week="0.6"),
    ):
        with pytest.raises(T.SettingsRuleError):
            T.check_settings(tt.body(), s, rec)
    with pytest.raises(T.SettingsRuleError):
        T.check_body_fat(Decimal("2.9"), rec)
    exempt = {"version", "energy.equation", "protein.ibw.formula"}
    unread = set(leaves(cfg.targets)) - read - exempt
    assert not unread, f"unread targets.yaml keys: {sorted(unread)}"


def test_asserted_at_load_keys():
    cfg = load_config()
    assert cfg.targets["version"] == 1
    assert cfg.targets["energy"]["equation"] == "mifflin_st_jeor_1990"
    assert cfg.targets["protein"]["ibw"]["formula"] == "devine"


def test_min_age_matches_protein_min_age():
    cfg = load_config()
    t = cfg.targets
    assert (
        t["minors"]["min_age_for_targets"]
        == cfg.thresholds["daily_limits"]["protein_min_age"]
        == t["energy"]["mifflin"]["valid_age"]["min"]
    )


def _imports(path: Path) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module)
            out.update(f"{node.module}.{a.name}" for a in node.names)
    return out


def _file(mod: str) -> Path | None:
    p = ROOT.joinpath(*mod.split("."))
    if p.with_suffix(".py").exists():
        return p.with_suffix(".py")
    return None


def _reach(start: str) -> set[str]:
    """Modules reachable from ``start``, following only app.scoring modules (package
    __init__ re-exports are checked separately below)."""
    seen: set[str] = set()
    todo = [start]
    while todo:
        mod = todo.pop()
        if mod in seen:
            continue
        seen.add(mod)
        f = _file(mod)
        if f is None:
            continue
        for imp in _imports(f):
            if imp.startswith("app.scoring.") and imp not in seen:
                todo.append(imp)
    return seen


@pytest.mark.parametrize("start", ["app.scoring.verdict", "app.scoring.conditions"])
def test_verdict_does_not_import_targets(start):
    assert "app.scoring.targets" not in _reach(start)


def test_analyze_service_does_not_import_targets():
    f = _file("app.features.analyze.service")
    imports = _imports(f)
    assert "app.scoring.targets" not in imports
    assert "app.features.targets" not in " ".join(imports)
    # and what it takes from app.scoring never reaches targets
    for imp in imports:
        if imp.startswith("app.scoring."):
            assert "app.scoring.targets" not in _reach(imp)


def test_package_root_does_not_reexport_targets():
    imports = _imports(ROOT / "app" / "scoring" / "__init__.py")
    assert not any(i.endswith("targets") for i in imports)

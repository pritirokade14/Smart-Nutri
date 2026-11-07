"""The diary never changes a verdict (Plan 11 Task 7; AGENTS rule 1): `POST /v1/analyze` is
identical before and after diary data, and the verdict modules never import the diary."""

import ast
import json
from pathlib import Path

import pytest

from scripts.export_fixture_responses import fixture_product_record
from tests.api.diary.conftest import ACC_A, G1_SETTINGS

ROOT = Path(__file__).resolve().parents[3]
NAMES = [
    "cola",
    "curd",
    "kiwi_yogurt",
    "namkeen",
    "no_ingredients",
    "oats",
    "sf_biscuit",
    "water",
    "whey_powder",
]


@pytest.mark.parametrize("name", NAMES)
async def test_diary_never_changes_verdicts(
    client, login, grant, db_session, set_primary, clock, name
):
    await grant(ACC_A, ["terms", "health_data"])  # no ai_processing: no explanation call
    login(ACC_A)
    await set_primary(birth_year=1997, sex="male", height_cm=175, weight_kg=70, goal="build_muscle")
    product = fixture_product_record(name)
    db_session.add(product)
    await db_session.flush()

    async def analyze() -> str:
        r = await client.post("/v1/analyze", json={"product_id": str(product.id)})
        assert r.status_code == 200, r.text
        body = r.json()
        body.pop("scan_id")  # a new scan row (random id) per call; everything else must match
        return json.dumps(body, sort_keys=True)

    before = await analyze()
    # Entries, a quick add, a frozen row, a custom slot-like state (archived), partial days.
    assert (await client.put("/v1/targets/settings", json=G1_SETTINGS)).status_code == 200
    log = await client.post("/v1/meals", json={"product_id": str(product.id), "grams": 30})
    assert log.status_code == 201
    assert (await client.post("/v1/meals", json={"quick": {"energy_kcal": 400}})).status_code == 201
    assert (await client.get("/v1/diary/day")).status_code == 200
    assert (await client.get("/v1/diary/week")).status_code == 200
    await client.put("/v1/diary/days/2026-11-05/status", json={"partial_logged": True})
    after = await analyze()
    assert before == after
    assert json.loads(after)["verdicts"]


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
    if (p / "__init__.py").exists():
        return p / "__init__.py"
    return None


def _reach(start: str) -> set[str]:
    """Every `app.*` module reachable from ``start`` through imports (transitively)."""
    seen: set[str] = set()
    todo = [start]
    while todo:
        mod = todo.pop()
        if mod in seen:
            continue
        seen.add(mod)
        path = _file(mod)
        if path is None:
            continue
        todo.extend(i for i in _imports(path) if i.startswith("app.") and i not in seen)
    return seen


@pytest.mark.parametrize("start", ["app.scoring.verdict", "app.features.analyze.service"])
def test_verdict_modules_never_import_diary(start):
    reached = _reach(start)
    assert len(reached) > 20  # the walker really followed the imports
    banned = [
        m
        for m in reached
        if m.startswith(("app.features.diary", "app.features.meal_slots", "app.features.targets"))
    ]
    assert banned == []

"""CLI pieces with FakeLLM. No network, no photos, no spend."""

from __future__ import annotations

import asyncio
import json

from app.features.scans.schemas import NutritionExtraction
from app.integrations.providers import ExtractionFailed
from scripts import label_eval
from tests.evals.test_label_eval_core import NULL_COL, pred
from tests.fakes.llm import FakeLLM


def _photos(tmp_path):
    img = tmp_path / "a.jpg"
    img.write_bytes(b"x")
    return [{"id": "a", "path": img, "conditions": [], "expected": {"per_100g": {"sugars_g": 10}}}]


def test_run_model_and_report_with_fake_llm(tmp_path):
    fake = FakeLLM(
        NutritionExtraction.model_validate(
            pred(
                per_100g={**NULL_COL, "sugars_g": 10},
                product_name=None,
                brand=None,
                veg_mark=None,
                category_guess=None,
            )
        )
    )
    photos = _photos(tmp_path)
    rows = asyncio.run(label_eval.run_model(fake, photos, "m", "extraction_v1", tmp_path / "raw"))
    assert fake.calls == 1 and fake.last_kwargs["model"] == "m"
    assert (tmp_path / "raw" / "a.json").exists()
    agg = label_eval.write_report("m", "extraction_v1", photos, rows, None, tmp_path / "rep", "d")
    assert agg["metrics"]["numeric_accuracy"] == 1.0
    assert (tmp_path / "rep" / "d_m_extraction_v1.md").exists()
    assert json.loads((tmp_path / "rep" / "d_m_extraction_v1.json").read_text())["photos"]


def test_run_model_v2_parses_cells_and_keeps_the_raw_output(tmp_path):
    from app.features.scans.schemas import CellIn, NutrientCellsIn, NutritionExtractionV2

    cells = dict.fromkeys(NutrientCellsIn.model_fields) | {
        "sugars_g": CellIn(printed="१०", unit_label="g")
    }
    raw = NutritionExtractionV2(
        product_name=None, brand=None, basis_detected="per_100g",
        per_100g=NutrientCellsIn(**cells), per_serving=None, per_100_unit="g",
        serving_size=None, ingredients=[], allergen_statement=None,
        may_contain_statement=None, claims=[], veg_mark=None, category_guess=None,
        confidence=0.9, unreadable_fields=[],
    )  # fmt: skip
    fake = FakeLLM(raw)
    photos = _photos(tmp_path)
    rows = asyncio.run(label_eval.run_model(fake, photos, "m", "extraction_v2", tmp_path / "raw"))
    assert fake.last_kwargs["schema"] is NutritionExtractionV2
    assert rows[0]["pred"]["per_100g"]["sugars_g"] == 10.0  # scored as parsed values
    saved = json.loads((tmp_path / "raw" / "a.json").read_text(encoding="utf-8"))
    assert saved["per_100g"]["sugars_g"]["printed"] == "१०"  # the raw cells are kept
    agg = label_eval.write_report("m", "extraction_v2", photos, rows, None, tmp_path / "rep", "d")
    assert agg["metrics"]["numeric_accuracy"] == 1.0


def test_run_model_records_failure(tmp_path):
    fake = FakeLLM(ExtractionFailed("x"))
    rows = asyncio.run(label_eval.run_model(fake, _photos(tmp_path), "m", "extraction_v1"))
    assert rows[0]["ok"] is False and rows[0]["error"] == "ExtractionFailed"


def test_cli_refuses_without_yes_spend(tmp_path, capsys, monkeypatch):
    (tmp_path / "a.jpg").write_bytes(b"x")
    man = tmp_path / "manifest.json"
    man.write_text(
        json.dumps({"version": 1, "photos": [{"id": "a", "image": "a.jpg", "expected": {}}]})
    )

    def boom(**_):
        raise AssertionError("network client built")

    monkeypatch.setattr("app.integrations.callmissed.CallMissedClient", boom)
    code = label_eval.main(["--models", "m1,m2", "--manifest", str(man)])
    out = capsys.readouterr().out
    assert code == 2 and "TOTAL 2 paid" in out and "--yes-spend" in out


def test_cli_with_no_photos_makes_no_calls(tmp_path):
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"version": 1, "photos": []}))
    assert label_eval.main(["--models", "m", "--manifest", str(man), "--yes-spend"]) == 1

import json
import shutil
import sys
from pathlib import Path

import pytest

from tests.fixtures.loader import FIXTURES, load_member, load_product

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
import generate_fixture_expectations as gen


def _tree(tmp_path: Path) -> Path:
    for kind in ("products", "members"):
        (tmp_path / kind).mkdir()
    return tmp_path


def _put(base: Path, kind: str, name: str, data: dict) -> None:
    (base / kind / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


def test_unknown_product_key_rejected(tmp_path):
    base = _tree(tmp_path)
    _put(base, "products", "x", {"name": "X", "category": "general", "bogus": 1})
    with pytest.raises(ValueError, match=r"x\.json.*bogus"):
        load_product("x", base)


def test_unknown_nutrient_key_rejected(tmp_path):
    base = _tree(tmp_path)
    _put(base, "products", "x", {"name": "X", "category": "general", "per_100g": {"salt": 1}})
    with pytest.raises(ValueError, match="salt"):
        load_product("x", base)


def test_missing_category_rejected(tmp_path):
    base = _tree(tmp_path)
    _put(base, "products", "x", {"name": "X"})
    with pytest.raises(ValueError, match="category"):
        load_product("x", base)


def test_extraction_confidence_passed_through(tmp_path):
    base = _tree(tmp_path)
    _put(
        base,
        "products",
        "x",
        {"name": "X", "category": "general", "extraction_confidence": 0.5, "source": "t"},
    )
    assert load_product("x", base).extraction_confidence == 0.5


def test_unknown_member_key_rejected(tmp_path):
    base = _tree(tmp_path)
    _put(base, "members", "m", {"id": "m", "name": "M", "diet": "veg", "label": "x"})
    with pytest.raises(ValueError, match=r"m\.json.*label"):
        load_member("m", base)


def test_missing_diet_rejected(tmp_path):
    base = _tree(tmp_path)
    _put(base, "members", "m", {"id": "m", "name": "M"})
    with pytest.raises(ValueError, match="diet"):
        load_member("m", base)


def test_generator_check_matches_committed():
    assert gen.main(["--check"]) == 0


def test_generator_check_and_write_on_copy(tmp_path):
    base = tmp_path / "fx"
    shutil.copytree(FIXTURES, base)
    assert gen.changes(base)[2] == {}
    victim = next((base / "expected").glob("*.json"))
    victim.write_text("{}\n", encoding="utf-8")
    extra = base / "expected" / "zzz.stale.json"
    extra.write_text("{}\n", encoding="utf-8")
    (base / "expected" / "water.no_age.json").unlink()
    tags = gen.changes(base)[2]
    assert set(tags.values()) == {"CHANGED", "REMOVED", "ADDED"}
    gen.write(base)
    assert gen.changes(base)[2] == {}
    assert not extra.exists()

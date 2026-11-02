from pathlib import Path

import yaml

_DATA = Path(__file__).parents[3] / "app" / "scoring" / "data"


def _load(name):
    return yaml.safe_load((_DATA / name).read_text(encoding="utf-8"))


def test_dairy_is_superset_of_milk_allergen_terms():
    assert set(_load("allergens.yaml")["milk"]["contains"]) <= set(_load("diet.yaml")["dairy"])


def test_dairy_includes_post_review_milk_terms():
    required = {
        "dairy whitener", "mawa", "lactitol", "ins966", "milk fat", "butter oil", "मक्खन", "मलाई",
        "खोया", "khoa", "khoya", "chhena", "दूध", "घी", "पनीर", "दही",
    }
    assert required <= set(_load("diet.yaml")["dairy"])


def test_headers_flag_pending_review():
    for name in ("diet.yaml", "ingredients.yaml"):
        first = (_DATA / name).read_text(encoding="utf-8").splitlines()[0]
        assert first.startswith("# PENDING DIETITIAN/CLINICIAN REVIEW")

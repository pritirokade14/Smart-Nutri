from app.scoring.config import load_config


def test_config_loads_all_sections():
    cfg = load_config()
    assert set(cfg.allergens) == {
        "milk",
        "peanut",
        "gluten",
        "soy",
        "egg",
        "tree_nut",
        "sesame",
        "fish",
        "crustacean",
        "mustard",
        "sulphite",
    }
    assert cfg.thresholds["min_extraction_confidence"] == 0.7
    assert "maltodextrin" in cfg.ingredient_lists["hidden_sugars"]
    assert "onion" in cfg.diet["jain_exclusions"]

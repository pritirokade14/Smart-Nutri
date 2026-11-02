# Plan 1: Rules Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, fully unit-tested Python rules engine (`apps/api/app/scoring`). Given a product's nutrition, ingredients and claims, plus a list of family members, it returns a product report and a verdict (`ok` / `caution` / `unknown` / `avoid`) with coded reasons for each member.

**Architecture:**
- Pure functions over frozen dataclasses. No I/O except loading four bundled YAML data files once.
- Reasons are codes with params, never prose. Plan 2's API and the LLM turn them into localised text.
- This plan also replaces the old backend with a fresh `uv` project. Plan 2 builds the API around this package.

**Tech Stack:** Python 3.13, `uv`, PyYAML, pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md` (§6 Rules Engine Requirements)

## Global Constraints

- Python `>=3.13`. The only runtime dependency in this plan is `pyyaml>=6.0.2`. Dev dependencies are `pytest>=8` and `ruff>=0.8`.
- All nutrient inputs are **per 100 g (or 100 ml)**. Derived values:
  - `salt_g = sodium_mg × 2.5 / 1000`
  - `kJ = kcal × 4.184`
- Status ranking for combining reasons: `avoid` (3) > `unknown` (2) > `caution` (1) > `ok` (0). The highest rank wins. With no reasons, the status is `ok`.
- **Never `ok` for an allergic member when ingredients are unknown.** Ingredients count as known when the list is non-empty and `extraction_confidence >= 0.7`.
- Canonical allergen keys:
  `milk, peanut, gluten, soy, egg, tree_nut, sesame, fish, crustacean, mustard, sulphite`.
- Diet values: `veg, eggetarian, vegan, jain, non_veg`.
- Condition values: `diabetes, prediabetes, pcos, hypertension, weight_loss`. The goal `"weight_loss"` counts as the condition.
- Every threshold lives in `app/scoring/data/thresholds.yaml`, which carries the comment `# PENDING CLINICIAN REVIEW`. Nothing threshold-like is hard-coded in `.py` files, except the Nutri-Score 2023 tables (an official algorithm).
- The Nutri-Score result is a computed approximation. Plan 2's API must label it "calculated by SmartNutri".
- All commands run from `apps/api/`: `uv run pytest ...`.

## Review Focus

1. **Ingredient lists in Devanagari.** Example: `["मूंगफली", "चीनी"]` must still flag peanut and added sugar. Owned by Task 3 (terms) and Task 6 (test).
2. **Implausible extracted values.** Example: sugars 250 g/100 g, or energy 4,000 kcal/100 g, from a per-pack misread. These must be treated as missing (which leads to `unknown`), not scored. Owned by Task 2.
3. **Member with no age (`age=None`).** Child and infant rules are skipped, with no crash. Owned by Task 9.
4. **Member allergen outside the canonical list** (for example `"kiwi"` from the "Other" chip). It must still be matched literally against the ingredients. Owned by Task 6.
5. **Odd claim formatting.** Examples: `"SUGAR-FREE!"`, `"No Added Sugars*"`. These must still be recognised. Owned by Task 8.

## File Map

```
apps/api/
  pyproject.toml                      # Task 1
  app/__init__.py                     # Task 1
  app/scoring/__init__.py             # Task 1 (empty) → Task 10 (exports)
  app/scoring/models.py               # Task 2  dataclasses + enums
  app/scoring/config.py               # Task 3  YAML loader
  app/scoring/ingredients.py          # Task 3  normalise + term matching
  app/scoring/data/allergens.yaml     # Task 3
  app/scoring/data/diet.yaml          # Task 3
  app/scoring/data/ingredients.yaml   # Task 3
  app/scoring/data/thresholds.yaml    # Task 3
  app/scoring/nutriscore.py           # Task 4
  app/scoring/warnings.py             # Task 5  high-in + hidden sugars + sodium additives
  app/scoring/allergens.py            # Task 6
  app/scoring/diet.py                 # Task 7
  app/scoring/claims.py               # Task 8
  app/scoring/conditions.py           # Task 9
  app/scoring/verdict.py              # Task 10 report builder, member verdicts, analyze()
  tests/unit/scoring/conftest.py      # Task 2  sample products and members
  tests/unit/scoring/test_*.py        # one per module
```

---

### Task 1: Replace the old backend with a fresh `uv` project

**Files:**
- Delete:
  - `apps/api/main.py`, `apps/api/requirements.txt`
  - `apps/api/ai/`, `apps/api/api/`, `apps/api/database/`, `apps/api/services/`
- Create:
  - `apps/api/pyproject.toml`
  - `apps/api/app/__init__.py`, `apps/api/app/scoring/__init__.py`
  - `apps/api/tests/unit/scoring/test_smoke.py`

**Interfaces:** Produces the `app.scoring` package, importable from tests.

- [ ] **Step 1: Delete the old backend code**

```bash
git rm -r apps/api/main.py apps/api/requirements.txt apps/api/ai apps/api/api apps/api/database apps/api/services
```

Expected: the files are staged as deleted. Their prompts remain readable in `main` branch history, which Plan 2 will reuse.

- [ ] **Step 2: Create `apps/api/pyproject.toml`**

```toml
[project]
name = "smartnutri-backend"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = ["pyyaml>=6.0.2"]

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.8"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py313"
```

Then create empty `app/__init__.py` and `app/scoring/__init__.py`.

- [ ] **Step 3: Write the smoke test** in `tests/unit/scoring/test_smoke.py`

```python
def test_scoring_package_imports():
    import app.scoring  # noqa: F401
```

- [ ] **Step 4: Install and run**

Run: `uv python install 3.13 && uv sync && uv run pytest -v`
Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add -A apps/api
git commit -m "chore(backend): replace prototype with fresh uv project for v1 rebuild"
```

---

### Task 2: Domain models

**Files:**
- Create: `apps/api/app/scoring/models.py`, `apps/api/tests/unit/scoring/conftest.py`, `apps/api/tests/unit/scoring/test_models.py`

**Interfaces:** Produces the following. Every later task uses these names exactly.

```python
class Category(StrEnum): GENERAL="general"; BEVERAGE="beverage"; WATER="water"; CHEESE="cheese"; FAT="fat"
class Status(StrEnum): OK="ok"; CAUTION="caution"; UNKNOWN="unknown"; AVOID="avoid"
    # property rank -> int  (ok 0, caution 1, unknown 2, avoid 3)
class AllergenState(StrEnum): CONTAINS="contains"; MAY_CONTAIN="may_contain"; UNKNOWN="unknown"
class Diet(StrEnum): VEG="veg"; EGGETARIAN="eggetarian"; VEGAN="vegan"; JAIN="jain"; NON_VEG="non_veg"
class ClaimVerdict(StrEnum): SUPPORTED="supported"; CONTRADICTED="contradicted"; UNVERIFIABLE="unverifiable"

@dataclass(frozen=True, slots=True)
class Nutrients:            # per 100 g / 100 ml; None = unknown
    energy_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    sugars_g: float | None = None
    fat_g: float | None = None
    sat_fat_g: float | None = None
    fiber_g: float | None = None
    salt_g: float | None = None
    sodium_mg: float | None = None
    fvl_percent: float | None = None   # fruit/veg/legume %
    def salt(self) -> float | None        # salt_g, else sodium_mg*2.5/1000, else None
    def energy_kj(self) -> float | None   # energy_kcal*4.184
    def sanitized(self) -> tuple["Nutrients", tuple[str, ...]]
        # returns copy with implausible fields set to None + names of dropped fields

@dataclass(frozen=True, slots=True)
class Product:
    name: str
    category: Category = Category.GENERAL
    per_100g: Nutrients = Nutrients()
    serving_size_g: float | None = None
    ingredients: tuple[str, ...] = ()
    allergen_statement: str | None = None      # "Contains: milk, soy"
    may_contain_statement: str | None = None   # "May contain traces of nuts"
    claims: tuple[str, ...] = ()
    veg_mark: Literal["veg", "non_veg"] | None = None
    contains_sweeteners: bool = False
    extraction_confidence: float = 1.0
    @property is_drink -> bool                 # category in (BEVERAGE, WATER)
    def per_serving(self, value_per_100g: float | None) -> float | None
        # value * serving_size_g / 100; None if either is None

@dataclass(frozen=True, slots=True)
class Member:
    id: str
    name: str
    age: int | None = None
    diet: Diet = Diet.NON_VEG
    allergens: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    goal: str | None = None

@dataclass(frozen=True, slots=True)
class Reason:
    code: str
    severity: Status
    params: Mapping[str, Any] = field(default_factory=dict)
```

The `sanitized()` plausibility bounds are fixed:
- Every `*_g` field must be in `[0, 100]`.
- `sodium_mg` must be in `[0, 40000]`.
- `energy_kcal` must be in `[0, 900]`.
- `fvl_percent` must be in `[0, 100]`.

The `conftest.py` fixtures are named products and members, used from Task 4 onward. The values below are exact.

| fixture | category | kcal | protein | carbs | sugars | fat | sat | fiber | salt | serving | ingredients | claims |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `sf_biscuit` | general | 450 | 8 | 72 | 2.0 | 15 | 7 | 2 | 0.9 | 25 | `("wheat flour (maida)", "maltodextrin", "edible vegetable oil (palm)", "milk solids", "raising agent (ins 500(ii))", "salt", "emulsifier (ins 322)")` | `("Sugar Free",)` |
| `namkeen` | general | 550 | 15 | 40 | 3 | 35 | 10 | 5 | 2.5 | 30 | `("gram flour (besan)", "edible vegetable oil", "peanuts", "salt", "spices", "onion powder", "garlic powder")` | `()` |
| `curd` | general | 60 | 3.5 | 4.7 | 4.0 | 3.1 | 2.0 | 0 | 0.1 | 100 | `("pasteurised toned milk", "active cultures")` | `()` |
| `oats` | general | 389 | 13 | 66 | 1.0 | 7 | 1.2 | 10.6 | 0.01 | 40 | `("whole grain rolled oats",)` | `("High Protein",)` |
| `cola` | beverage | 42 | 0 | 10.6 | 10.6 | 0 | 0 | 0 | 0 | 300 | `("carbonated water", "sugar", "caffeine")` | `()` |
| `water` | water | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 500 | `("water",)` | `()` |
| `no_ingredients` | general | 400 | 5 | 60 | 10 | 15 | 5 | 2 | 1.0 | None | `()` | `()` |

Members:
- `diabetic_adult(id="m1", age=52, diet=VEG, conditions=("diabetes",))`
- `milk_allergic_child(id="m2", age=8, diet=VEG, allergens=("milk",))`
- `jain_adult(id="m3", age=40, diet=JAIN)`
- `bp_parent(id="m4", age=70, conditions=("hypertension",))`
- `peanut_allergic(id="m5", age=30, allergens=("peanut",))`
- `vegan_adult(id="m6", age=28, diet=VEGAN)`
- `weight_loss_adult(id="m7", age=35, goal="weight_loss")`
- `infant(id="m8", age=1)`
- `no_age(id="m9", age=None)`

- [ ] **Step 1: Write failing tests** in `test_models.py`

```python
def test_salt_derived_from_sodium():
    assert Nutrients(sodium_mg=400).salt() == pytest.approx(1.0)

def test_salt_prefers_explicit_value():
    assert Nutrients(salt_g=0.5, sodium_mg=400).salt() == 0.5

def test_energy_kj():
    assert Nutrients(energy_kcal=100).energy_kj() == pytest.approx(418.4)

def test_status_rank_order():
    assert [s.rank for s in (Status.OK, Status.CAUTION, Status.UNKNOWN, Status.AVOID)] == [0, 1, 2, 3]

def test_per_serving(sf_biscuit):
    assert sf_biscuit.per_serving(2.0) == pytest.approx(0.5)
    assert replace(sf_biscuit, serving_size_g=None).per_serving(2.0) is None

def test_sanitized_drops_implausible_values():
    clean, dropped = Nutrients(sugars_g=250, energy_kcal=4000, protein_g=10).sanitized()
    assert clean.sugars_g is None and clean.energy_kcal is None and clean.protein_g == 10
    assert set(dropped) == {"sugars_g", "energy_kcal"}

def test_is_drink(cola, water, curd):
    assert cola.is_drink and water.is_drink and not curd.is_drink
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/unit/scoring/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: app.scoring.models`.

- [ ] **Step 3: Implement `app/scoring/models.py` and `conftest.py`** exactly as in the Interfaces block and the fixture table above.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/scoring/test_models.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/scoring/models.py apps/api/tests/unit/scoring/
git commit -m "feat(scoring): domain models, plausibility checks and test fixtures"
```

---

### Task 3: Data files, config loader and ingredient matcher

**Files:**
- Create:
  - `apps/api/app/scoring/config.py`, `apps/api/app/scoring/ingredients.py`
  - `apps/api/app/scoring/data/{allergens,diet,ingredients,thresholds}.yaml`
  - `apps/api/tests/unit/scoring/test_ingredients.py`, `apps/api/tests/unit/scoring/test_config.py`
- Modify: `apps/api/tests/unit/scoring/conftest.py` (add `cfg` fixture)

**Interfaces:** Produces:

```python
# config.py
@dataclass(frozen=True)
class ScoringConfig:
    allergens: Mapping[str, Mapping[str, list[str]]]   # key -> {"contains": [...], "possible": [...], "exclude": [...]}
    diet: Mapping[str, list[str]]                       # non_veg, egg, dairy, animal_other, jain_exclusions
    ingredient_lists: Mapping[str, list[str]]           # added_sugars, hidden_sugars, sodium_additives, caffeine, salt
    thresholds: Mapping[str, Any]                       # thresholds.yaml as loaded
def load_config(data_dir: Path | None = None) -> ScoringConfig   # cached when data_dir is None

# ingredients.py
def normalize(text: str) -> str
def find_terms(texts: Iterable[str], terms: Iterable[str], exclude: Iterable[str] = ()) -> list[str]
```

Matching rules for `normalize`:
- Apply NFKC and lowercase.
- Rewrite `e322`, `e-322`, `ins 322`, `ins-322` and `ins 500(ii)` to `ins322` / `ins500`.
- Rewrite a bare `(322)` to `ins322`.
- Replace other punctuation with spaces and collapse whitespace.
- Keep Devanagari characters.

Matching rules for `find_terms`:
- Normalize the joined texts and remove every `exclude` phrase first.
- Match each normalized term on word boundaries, allowing an optional `s` or `es` plural suffix. Use `(?<!\w)` and `(?!\w)`, which work for Devanagari.
- Match **longest term first**, and blank out each match in the working text after recording it. That way `"onion powder"` reports only `"onion powder"`, not also `"onion"`.
- Return the sorted, de-duplicated matched terms, in their original spelling.

- [ ] **Step 1: Create the four data files with this exact content**

`data/allergens.yaml`:

```yaml
milk:       {contains: [milk, milk solids, milk powder, whey, casein, caseinate, lactose, butter, ghee, cream, cheese, paneer, khoya, khoa, curd, dahi, yoghurt, yogurt, malai, buttermilk, chhena, दूध, घी, पनीर, दही],
             possible: [], exclude: [coconut milk, almond milk, oat milk, cocoa butter, peanut butter, nut butter, shea butter, cream of tartar]}
peanut:     {contains: [peanut, groundnut, arachis oil, moongphali, मूंगफली], possible: [], exclude: []}
gluten:     {contains: [wheat, atta, maida, sooji, suji, semolina, rava, barley, rye, malt, malt extract, dalia, spelt, गेहूं, मैदा], possible: [oats, hing, asafoetida], exclude: []}
soy:        {contains: [soy, soya, soybean, soy lecithin, सोया], possible: [lecithin, ins322, vegetable protein], exclude: [sunflower lecithin]}
egg:        {contains: [egg, egg white, egg yolk, albumin, mayonnaise, अंडा], possible: [], exclude: [eggplant]}
tree_nut:   {contains: [almond, badam, cashew, kaju, pistachio, pista, walnut, akhrot, hazelnut, pecan, macadamia], possible: [nuts], exclude: [coconut, nutmeg]}
sesame:     {contains: [sesame, til, gingelly], possible: [], exclude: []}
fish:       {contains: [fish, anchovy, tuna, sardine, fish sauce, fish oil], possible: [], exclude: []}
crustacean: {contains: [prawn, shrimp, crab, lobster], possible: [], exclude: []}
mustard:    {contains: [mustard, rai, sarson], possible: [], exclude: []}
sulphite:   {contains: [sulphite, sulfite, metabisulphite, metabisulfite, ins220, ins221, ins222, ins223, ins224, ins225, ins226, ins227, ins228], possible: [], exclude: []}
```

`data/diet.yaml`:

```yaml
non_veg:         [chicken, mutton, beef, pork, lamb, meat, meat extract, fish, anchovy, prawn, shrimp, crab, gelatin, gelatine, lard, tallow, rennet, isinglass, carmine, cochineal, ins120, bone, fish oil, fish sauce]
egg:             [egg, egg white, egg yolk, albumin, mayonnaise, अंडा]
dairy:           [milk, milk solids, milk powder, whey, casein, caseinate, lactose, butter, ghee, cream, cheese, paneer, khoya, curd, dahi, yoghurt, yogurt, malai, buttermilk]
animal_other:    [honey, beeswax, ins901, shellac, ins904, lanolin]
jain_exclusions: [onion, garlic, potato, carrot, beetroot, radish, ginger, yam, sweet potato, arbi, प्याज, लहसुन, onion powder, garlic powder]
```

`data/ingredients.yaml`:

```yaml
added_sugars:     [sugar, cane sugar, brown sugar, jaggery, gur, khand, mishri, honey, चीनी, गुड़]
hidden_sugars:    [maltodextrin, dextrose, glucose, glucose syrup, liquid glucose, invert sugar, invert syrup, fructose, high fructose corn syrup, corn syrup, sucrose, malt extract, maltose, date syrup, fruit juice concentrate, golden syrup, molasses]
sodium_additives: [monosodium glutamate, ins621, sodium benzoate, ins211, sodium bicarbonate, baking soda, ins500, sodium nitrite, ins250, disodium inosinate, ins631, disodium guanylate, ins627, ins635, sodium citrate, ins331, sodium phosphate, ins339]
caffeine:         [caffeine, coffee, guarana]
salt:             [salt, iodised salt, rock salt, black salt, sendha namak, नमक]
```

`data/thresholds.yaml` (it starts with `# PENDING CLINICIAN REVIEW`):

```yaml
# PENDING CLINICIAN REVIEW — defaults from UK FSA (high-in), FSSAI Advertising & Claims Regs 2018 (claims), NHS (child sugar)
min_extraction_confidence: 0.7
allergen_may_contain_status: avoid
high_in:
  food:  {sugars_g: 22.5, fat_g: 17.5, sat_fat_g: 5.0, salt_g: 1.5}
  drink: {sugars_g: 11.25, fat_g: 8.75, sat_fat_g: 2.5, salt_g: 0.75}
claims:   # verify values against FSSAI (Advertising & Claims) Regulations 2018, Schedule I
  sugar_free_max_g: 0.5
  low_sugar_max_g: {food: 5.0, drink: 2.5}
  low_fat_max_g: {food: 3.0, drink: 1.5}
  low_sodium_max_mg: 120
  source_of_protein_min_energy_pct: 10
  high_protein_min_energy_pct: 20
conditions:
  blood_sugar:   # diabetes, prediabetes, pcos
    applies_to: [diabetes, prediabetes, pcos]
    avoid_sugars_g: 22.5
    caution_sugars_g: 5.0
    caution_carbs_per_serving_g: 30
  hypertension:
    applies_to: [hypertension]
    avoid_salt_g: 1.5
    caution_salt_g: 0.3
  weight_loss:
    applies_to: [weight_loss]
    caution_energy_kcal: 400
    caution_nutriscore: [D, E]
    good_protein_g_per_100kcal: 5
  child:          # 2 <= age < 13
    free_sugar_daily_limit_g: {2: 19, 7: 24, 11: 30}   # key = min age of band (NHS; 2–3 uses 4–6 value)
    caution_pct_of_limit: 25
    avoid_pct_of_limit: 50
  infant:         # age < 2
    max_age: 2
```

- [ ] **Step 2: Write failing tests**

```python
# test_ingredients.py
def test_normalize_ins_codes():
    n = normalize("Emulsifier (INS 322), E-471, raising agent (ins 500(ii)), stabiliser (412)")
    assert {"ins322", "ins471", "ins500", "ins412"} <= set(n.split())

def test_word_boundary_and_plural():
    assert find_terms(["roasted peanuts"], ["peanut"]) == ["peanut"]
    assert find_terms(["eggplant"], ["egg"]) == []

def test_exclude_phrases():
    assert find_terms(["cocoa butter", "sugar"], ["butter"], exclude=["cocoa butter"]) == []

def test_devanagari_terms():
    assert find_terms(["मूंगफली", "चीनी"], ["मूंगफली", "चीनी"]) == ["चीनी", "मूंगफली"]

def test_longest_match_consumes_text():
    assert find_terms(["liquid glucose", "salt"], ["liquid glucose", "glucose"]) == ["liquid glucose"]
    assert find_terms(["onion powder"], ["onion", "onion powder"]) == ["onion powder"]

# test_config.py
def test_config_loads_all_sections():
    cfg = load_config()
    assert set(cfg.allergens) == {"milk","peanut","gluten","soy","egg","tree_nut","sesame","fish","crustacean","mustard","sulphite"}
    assert cfg.thresholds["min_extraction_confidence"] == 0.7
    assert "maltodextrin" in cfg.ingredient_lists["hidden_sugars"]
    assert "onion" in cfg.diet["jain_exclusions"]
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run pytest tests/unit/scoring/test_ingredients.py tests/unit/scoring/test_config.py -v`
Expected: FAIL (modules missing).

- [ ] **Step 4: Implement `config.py` and `ingredients.py`** to the Interfaces block.
  - `load_config` reads YAML with `yaml.safe_load` and caches the default with `functools.cache`.
  - Data files ship as package data. Load them via `Path(__file__).parent / "data"`.
  - Add a session-scoped `cfg` fixture (`load_config()`) to `tests/unit/scoring/conftest.py`. Tasks 5–10 use it.

- [ ] **Step 5: Run the tests to verify they pass**, then commit

```bash
uv run pytest tests/unit/scoring -v
git add apps/api/app/scoring apps/api/tests/unit/scoring
git commit -m "feat(scoring): ingredient matcher, config loader and rule data"
```

---

### Task 4: Nutri-Score 2023

**Files:**
- Create: `apps/api/app/scoring/nutriscore.py`, `apps/api/tests/unit/scoring/test_nutriscore.py`

**Interfaces:**
- Consumes: `Product`, `Category`, `Nutrients` (Task 2).
- Produces:

```python
@dataclass(frozen=True, slots=True)
class NutriScoreResult:
    grade: Literal["A","B","C","D","E"] | None
    points: int | None
    partial: bool          # fibre/protein/fvl missing → counted as 0
    approximated: bool     # CHEESE/FAT scored with general table
    reason: str | None     # "insufficient_data" when grade is None
def compute_nutriscore(product: Product) -> NutriScoreResult
```

The 2023 tables below are pinned. Points equal the number of thresholds that the value **strictly exceeds**.

| component | general foods | beverages |
|---|---|---|
| energy kJ | 335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350 | 30, 90, 150, 210, 240, 270, 300, 330, 360, 390 |
| sugars g | 3.4, 6.8, 10, 14, 17, 20, 24, 27, 31, 34, 37, 41, 44, 48, 51 | 0, 1.5, 3, 4.5, 6, 7.5, 9, 10.5, 12, 13.5 |
| sat fat g | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | same as general |
| salt g | 0.2, 0.4 … 4.0 (step 0.2, 20 thresholds) | same as general |
| sweeteners | none | +4 if `contains_sweeteners` |
| protein g | 2.4, 4.8, 7.2, 9.6, 12, 14, 17 | 1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0 |
| fibre g | 3.0, 4.1, 5.2, 6.3, 7.4 | same as general |
| fvl % | >40 → 1, >60 → 2, >80 → 5 | >40 → 2, >60 → 4, >80 → 6 |
| protein rule | protein points = 0 when negative points ≥ 11 (not CHEESE) | protein always counted |
| grade | ≤0 A, 1–2 B, 3–10 C, 11–18 D, ≥19 E | WATER → A; ≤2 B, 3–6 C, 7–9 D, ≥10 E |

Missing data:
- If energy, sugars, saturated fat or salt (salt via `Nutrients.salt()`) is missing, return `grade=None, points=None, reason="insufficient_data"`.
- Missing fibre, protein or fvl counts as 0, with `partial=True`.
- CHEESE and FAT use the general table with `approximated=True`. Cheese is exempt from the protein rule.

- [ ] **Step 0: Verify the tables before coding.** Compare the table above with Open Food Facts' open-source implementation (`openfoodfacts-server`, `lib/ProductOpener/Nutriscore.pm`, the 2023 thresholds) or the Santé publique France 2023 update document.
  - If any value differs, use the official value.
  - Recompute the affected expectations in Step 1.
  - Record the source URL in a module docstring.

- [ ] **Step 1: Write failing tests**

```python
def test_curd_is_B(curd):                 # N=0+1+1+0=2, P=protein 1 → 1
    r = compute_nutriscore(curd); assert (r.grade, r.points, r.partial) == ("B", 1, True)

def test_sf_biscuit_is_D(sf_biscuit):     # 1883kJ→5, sugar 2→0, sat 7→6, salt .9→4 ⇒ N=15 → protein ignored; fibre 2→0 ⇒ 15 → D
    r = compute_nutriscore(sf_biscuit); assert (r.grade, r.points) == ("D", 15)

def test_namkeen_is_E(namkeen):           # 2301kJ→6, sugar 0, sat 10→9, salt 2.5→12 ⇒ 27; fibre 5→2 ⇒ 25
    r = compute_nutriscore(namkeen); assert (r.grade, r.points) == ("E", 25)

def test_oats_is_A(oats):                 # 1628kJ→4, sat 1.2→1 ⇒ 5; protein 13→5, fibre 10.6→5 ⇒ -5
    r = compute_nutriscore(oats); assert (r.grade, r.points) == ("A", -5)

def test_cola_beverage_is_E(cola):        # 176kJ→3, sugar 10.6→8 ⇒ 11
    r = compute_nutriscore(cola); assert (r.grade, r.points) == ("E", 11)

def test_water_is_A(water):
    assert compute_nutriscore(water).grade == "A"

def test_missing_sat_fat_is_insufficient(curd):
    r = compute_nutriscore(replace(curd, per_100g=replace(curd.per_100g, sat_fat_g=None)))
    assert (r.grade, r.reason) == (None, "insufficient_data")

def test_cheese_flagged_approximated(curd):
    assert compute_nutriscore(replace(curd, category=Category.CHEESE)).approximated is True
```

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/scoring/test_nutriscore.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement `compute_nutriscore`** using one helper, `_points(value: float, thresholds: Sequence[float]) -> int`, together with the tables as module constants.
- [ ] **Step 4: Run the tests to verify they pass.** Expected: all pass.
- [ ] **Step 5: Commit** with message `feat(scoring): Nutri-Score 2023 (general, beverage, water)`.

---

### Task 5: "High in" warnings, hidden sugars and sodium additives

**Files:**
- Create: `apps/api/app/scoring/warnings.py`, `apps/api/tests/unit/scoring/test_warnings.py`

**Interfaces:**
- Consumes: `Product` (Task 2), `ScoringConfig` and `find_terms` (Task 3).
- Produces:

```python
def high_in(product: Product, cfg: ScoringConfig) -> tuple[str, ...]
    # subset of ("sugar","fat","sat_fat","salt") in that order; drink table when product.is_drink
def hidden_sugars(product: Product, cfg: ScoringConfig) -> tuple[str, ...]
def added_sugar_terms(product: Product, cfg: ScoringConfig) -> tuple[str, ...]  # added_sugars ∪ hidden_sugars matches
def sodium_additives(product: Product, cfg: ScoringConfig) -> tuple[str, ...]
def ingredient_hits(product: Product, cfg: ScoringConfig, list_name: str) -> tuple[str, ...]  # generic, used by Task 9 (caffeine, salt)
```

A threshold is crossed when the value is **strictly greater** than it. Missing values never trigger a warning.

- [ ] **Step 1: Write failing tests**

```python
def test_high_in_biscuit(sf_biscuit, cfg):  assert high_in(sf_biscuit, cfg) == ("sat_fat",)
def test_high_in_namkeen(namkeen, cfg):     assert high_in(namkeen, cfg) == ("fat", "sat_fat", "salt")
def test_drink_threshold(cola, cfg):        assert high_in(cola, cfg) == ()  # 10.6 < 11.25
def test_drink_high_sugar(cola, cfg):
    assert high_in(replace(cola, per_100g=replace(cola.per_100g, sugars_g=12)), cfg) == ("sugar",)
def test_hidden_sugars(sf_biscuit, cfg):    assert hidden_sugars(sf_biscuit, cfg) == ("maltodextrin",)
def test_added_sugar_terms(cola, cfg):      assert added_sugar_terms(cola, cfg) == ("sugar",)
def test_sodium_additives(sf_biscuit, cfg): assert sodium_additives(sf_biscuit, cfg) == ("ins500",)
```

The `cfg` fixture already exists in `conftest.py` (added by Task 3).

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/scoring/test_warnings.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** to the Interfaces block. Each function returns a sorted tuple, except `high_in`, which uses the fixed order.
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(scoring): high-in warnings, hidden sugars, sodium additives`.

---

### Task 6: Allergen detection

**Files:**
- Create: `apps/api/app/scoring/allergens.py`, `apps/api/tests/unit/scoring/test_allergens.py`

**Interfaces:**
- Consumes: `Product`, `Member`, `Reason`, `Status`, `AllergenState` (Task 2), `ScoringConfig` and `find_terms` (Task 3).
- Produces:

```python
def ingredients_known(product: Product, cfg: ScoringConfig) -> bool
    # bool(product.ingredients) and product.extraction_confidence >= cfg.thresholds["min_extraction_confidence"]
def detect_allergens(product: Product, cfg: ScoringConfig, extra_keys: Iterable[str] = ()) -> dict[str, AllergenState]
    # only detected keys; contains beats may_contain
def allergen_reasons(product: Product, member: Member, cfg: ScoringConfig) -> list[Reason]
```

Detection rules:
1. A match in `ingredients` or `allergen_statement` against `contains` terms gives `CONTAINS`.
2. A match against `possible` terms in `ingredients`, or any `contains` / `possible` term in `may_contain_statement`, gives `MAY_CONTAIN`.
3. Each allergen's `exclude` phrases are removed before matching.
4. Keys in `extra_keys` that are not in the config (for example `"kiwi"`) are matched literally as a single `contains` term.

Member reasons:

| condition | code | severity | params |
|---|---|---|---|
| state `CONTAINS` | `allergen_contains` | `AVOID` | `{"allergen": key}` |
| state `MAY_CONTAIN` | `allergen_may_contain` | `Status(cfg.thresholds["allergen_may_contain_status"])`, default `AVOID` | `{"allergen": key}` |
| not detected and not `ingredients_known` | `allergen_unknown` | `UNKNOWN` | `{"allergen": key}` |

- [ ] **Step 1: Write failing tests**

```python
def test_biscuit_contains_milk_and_gluten_may_contain_soy(sf_biscuit, cfg):
    d = detect_allergens(sf_biscuit, cfg)
    assert d["milk"] == AllergenState.CONTAINS and d["gluten"] == AllergenState.CONTAINS
    assert d["soy"] == AllergenState.MAY_CONTAIN          # bare "ins 322"

def test_may_contain_statement(curd, cfg):
    p = replace(curd, may_contain_statement="May contain traces of nuts and peanuts")
    d = detect_allergens(p, cfg)
    assert d["peanut"] == AllergenState.MAY_CONTAIN and d["tree_nut"] == AllergenState.MAY_CONTAIN

def test_coconut_milk_is_not_milk(curd, cfg):
    assert "milk" not in detect_allergens(replace(curd, ingredients=("coconut milk", "sugar")), cfg)

def test_hindi_peanut(curd, cfg):
    assert detect_allergens(replace(curd, ingredients=("मूंगफली", "नमक")), cfg)["peanut"] == AllergenState.CONTAINS

def test_custom_allergen_matched_literally(curd, cfg, peanut_allergic):
    p = replace(curd, ingredients=("kiwi pulp", "sugar"))
    m = replace(peanut_allergic, allergens=("kiwi",))
    assert [r.code for r in allergen_reasons(p, m, cfg)] == ["allergen_contains"]

def test_unknown_ingredients_never_ok(no_ingredients, cfg, peanut_allergic):
    rs = allergen_reasons(no_ingredients, peanut_allergic, cfg)
    assert [(r.code, r.severity) for r in rs] == [("allergen_unknown", Status.UNKNOWN)]

def test_low_confidence_is_unknown(namkeen, cfg, milk_allergic_child):
    rs = allergen_reasons(replace(namkeen, extraction_confidence=0.5), milk_allergic_child, cfg)
    assert rs[0].code == "allergen_unknown"

def test_peanut_allergy_on_namkeen(namkeen, cfg, peanut_allergic):
    assert allergen_reasons(namkeen, peanut_allergic, cfg)[0].severity == Status.AVOID
```

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/scoring/test_allergens.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** to the Interfaces block and the rules table.
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(scoring): tri-state allergen detection with synonyms`.

---

### Task 7: Diet checks

**Files:**
- Create: `apps/api/app/scoring/diet.py`, `apps/api/tests/unit/scoring/test_diet.py`

**Interfaces:**
- Consumes: Task 2 models, `find_terms`, and `ingredients_known` (Task 6).
- Produces:

```python
def diet_violations(product: Product, cfg: ScoringConfig) -> dict[Diet, tuple[str, ...]]
    # every Diet key present; NON_VEG always ()
def veg_mark_mismatch(product: Product, cfg: ScoringConfig) -> bool
    # product.veg_mark == "veg" and diet_violations[VEG] non-empty
def diet_reasons(product: Product, member: Member, cfg: ScoringConfig) -> list[Reason]
```

Term sets per diet, as unions of the lists in `diet.yaml`:

| diet | term lists |
|---|---|
| VEG | non_veg ∪ egg |
| EGGETARIAN | non_veg |
| VEGAN | non_veg ∪ egg ∪ dairy ∪ animal_other |
| JAIN | non_veg ∪ egg ∪ animal_other ∪ jain_exclusions |

Member reasons:
- If there are violations for `member.diet`, add `("diet_violation", AVOID, {"diet": diet, "ingredients": [...]})`.
- If ingredients are not known and the diet is not `non_veg`, add `("diet_unknown", UNKNOWN, {"diet": diet})`. Exception: VEG and EGGETARIAN members get no reason when `veg_mark == "veg"`.

- [ ] **Step 1: Write failing tests**

```python
def test_namkeen_not_jain(namkeen, cfg):
    assert diet_violations(namkeen, cfg)[Diet.JAIN] == ("garlic powder", "onion powder")
def test_curd_not_vegan(curd, cfg):
    assert diet_violations(curd, cfg)[Diet.VEGAN] == ("milk",)
def test_gelatin_breaks_veg_mark(curd, cfg):
    p = replace(curd, ingredients=("milk", "gelatin"), veg_mark="veg")
    assert veg_mark_mismatch(p, cfg) is True
def test_jain_member_avoids_namkeen(namkeen, cfg, jain_adult):
    assert diet_reasons(namkeen, jain_adult, cfg)[0].severity == Status.AVOID
def test_unknown_ingredients_with_veg_mark_ok_for_veg(no_ingredients, cfg, diabetic_adult):
    assert diet_reasons(replace(no_ingredients, veg_mark="veg"), diabetic_adult, cfg) == []
def test_unknown_ingredients_unknown_for_vegan(no_ingredients, cfg, vegan_adult):
    assert diet_reasons(no_ingredients, vegan_adult, cfg)[0].code == "diet_unknown"
```

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/scoring/test_diet.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `diet.py` to the Interfaces block and the term-set table.
- [ ] **Step 4: Run the whole scoring suite.** Run: `uv run pytest tests/unit/scoring -v`. Expected: all pass.
- [ ] **Step 5: Commit** with message `feat(scoring): veg/eggetarian/vegan/jain diet checks and veg-mark mismatch`.

---

### Task 8: Claim checker

**Files:**
- Create: `apps/api/app/scoring/claims.py`, `apps/api/tests/unit/scoring/test_claims.py`

**Interfaces:**
- Consumes: Task 2 models, `added_sugar_terms` (Task 5), `ingredients_known` (Task 6).
- Produces:

```python
@dataclass(frozen=True, slots=True)
class ClaimCheck:
    claim: str                 # canonical key
    verdict: ClaimVerdict
    reason_code: str
    params: Mapping[str, Any] = field(default_factory=dict)
def check_claims(product: Product, cfg: ScoringConfig) -> tuple[ClaimCheck, ...]   # order of product.claims; unrecognised claims skipped
```

Canonical claims and their patterns. Matching runs on `normalize(claim)`, and patterns are tried in this order:

| key | patterns | rule (`d` = drink limits when `is_drink`) |
|---|---|---|
| `no_added_sugar` | `no added sugar` | Contradicted (`added_sugar_ingredient`, `{"ingredients": [...]}`) if `added_sugar_terms` is non-empty. Unverifiable (`ingredients_unknown`) if ingredients are not known. Otherwise supported (`ok`). |
| `sugar_free` | `sugar free`, `zero sugar`, `no sugar` | `sugars_g ≤ sugar_free_max_g` |
| `low_sugar` | `low sugar` | `sugars_g ≤ low_sugar_max_g[d]` |
| `low_fat` | `low fat` | `fat_g ≤ low_fat_max_g[d]` |
| `low_sodium` | `low sodium`, `low salt` | `sodium_mg` (or `salt × 400`) `≤ low_sodium_max_mg` |
| `high_protein` | `high protein`, `protein rich` | `protein_g × 4 / energy_kcal × 100 ≥ high_protein_min_energy_pct` |
| `source_of_protein` | `source of protein`, `protein` | `≥ source_of_protein_min_energy_pct` |

Verdicts for the numeric rules:
- Pass: `SUPPORTED` with reason `ok`.
- Fail: `CONTRADICTED` with reason `exceeds_limit` or `below_minimum`, and params `{"value": v, "limit": l}`.
- A required value is missing: `UNVERIFIABLE` with reason `nutrient_missing`.

- [ ] **Step 1: Write failing tests**

```python
def test_sugar_free_biscuit_contradicted(sf_biscuit, cfg):
    (c,) = check_claims(sf_biscuit, cfg)
    assert (c.claim, c.verdict, c.reason_code) == ("sugar_free", ClaimVerdict.CONTRADICTED, "exceeds_limit")

def test_no_added_sugar_with_maltodextrin(sf_biscuit, cfg):
    (c,) = check_claims(replace(sf_biscuit, claims=("No Added Sugars*",)), cfg)
    assert c.verdict == ClaimVerdict.CONTRADICTED and c.params["ingredients"] == ["maltodextrin"]

def test_oats_high_protein_contradicted(oats, cfg):  # 13*4/389 = 13.4% → not high (20%)
    (c,) = check_claims(oats, cfg)
    assert (c.claim, c.verdict) == ("high_protein", ClaimVerdict.CONTRADICTED)

def test_shouting_claim_recognised(curd, cfg):
    (c,) = check_claims(replace(curd, claims=("SUGAR-FREE!",)), cfg)
    assert c.claim == "sugar_free"

def test_unrecognised_claim_skipped(curd, cfg):
    assert check_claims(replace(curd, claims=("Tasty!",)), cfg) == ()

def test_missing_nutrient_unverifiable(no_ingredients, cfg):
    p = replace(no_ingredients, claims=("low fat",), per_100g=replace(no_ingredients.per_100g, fat_g=None))
    assert check_claims(p, cfg)[0].verdict == ClaimVerdict.UNVERIFIABLE
```

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/scoring/test_claims.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** to the table above.
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(scoring): front-of-pack claim checker`.

---

### Task 9: Condition and goal rules

**Files:**
- Create: `apps/api/app/scoring/conditions.py`, `apps/api/tests/unit/scoring/test_conditions.py`

**Interfaces:**
- Consumes:
  - Task 2 models
  - `NutriScoreResult` (Task 4)
  - `high_in`, `hidden_sugars`, `added_sugar_terms`, `sodium_additives`, `ingredient_hits` (Task 5)
  - `ClaimCheck` (Task 8)
- Produces:

```python
def condition_reasons(product: Product, member: Member, nutriscore: NutriScoreResult,
                      claims: Sequence[ClaimCheck], cfg: ScoringConfig) -> list[Reason]
```

A member's active rule groups:
- Each `conditions.*.applies_to` entry that matches `member.conditions`, or `member.goal` for `weight_loss`.
- `child` when `2 ≤ age < 13`.
- `infant` when `age < 2`.
- `age=None` means neither the child nor the infant group applies.

Rules ("missing" means the value is `None`, which emits `("nutrient_missing", UNKNOWN, {"nutrient": name, "rule": group})` once per nutrient):

| group | rule | reason |
|---|---|---|
| blood_sugar | `sugars_g > avoid_sugars_g` | `sugar_high` · AVOID · `{"sugars_g"}` |
| blood_sugar | else `sugars_g > caution_sugars_g` | `sugar_moderate` · CAUTION |
| blood_sugar | any `sugar_free` / `low_sugar` / `no_added_sugar` claim `CONTRADICTED` | `misleading_sugar_claim` · AVOID · `{"claim"}` |
| blood_sugar | `hidden_sugars` non-empty | `hidden_sugars` · CAUTION · `{"ingredients"}` |
| blood_sugar | `per_serving(carbs_g) > caution_carbs_per_serving_g` | `carbs_per_serving_high` · CAUTION · `{"carbs_g"}` |
| hypertension | `salt > avoid_salt_g` | `salt_high` · AVOID |
| hypertension | else `salt > caution_salt_g` | `salt_moderate` · CAUTION |
| hypertension | `sodium_additives` non-empty | `sodium_additives` · CAUTION |
| weight_loss | `energy_kcal > caution_energy_kcal` | `energy_dense` · CAUTION |
| weight_loss | `nutriscore.grade in caution_nutriscore` | `nutriscore_low` · CAUTION · `{"grade"}` |
| weight_loss | `protein_g / energy_kcal × 100 ≥ good_protein_g_per_100kcal` | `good_protein_density` · OK |
| child | sugar per serving (or per 100 g when there is no serving) `> avoid_pct` of the age-band limit | `child_sugar_high` · AVOID · `{"pct", "limit_g"}` |
| child | else `> caution_pct` | `child_sugar_moderate` · CAUTION |
| child | `ingredient_hits(caffeine)` | `child_caffeine` · AVOID |
| child | `"salt" in high_in` | `salt_high` · CAUTION |
| infant | `added_sugar_terms` non-empty | `infant_added_sugar` · AVOID |
| infant | `ingredient_hits(salt)` non-empty | `infant_added_salt` · AVOID |
| infant | `"honey"` in added-sugar hits | `infant_honey` · AVOID |

- [ ] **Step 1: Write failing tests**

```python
def test_diabetic_and_sugar_free_biscuit(sf_biscuit, diabetic_adult, cfg):
    # carbs per serving 72*25/100 = 18 g → not > 30
    assert _codes(sf_biscuit, diabetic_adult, cfg) == {"misleading_sugar_claim", "hidden_sugars"}

def test_diabetic_and_curd_ok(curd, diabetic_adult, cfg):
    assert _codes(curd, diabetic_adult, cfg) == set()          # 4.0 g ≤ 5.0

def test_bp_parent_and_namkeen(namkeen, bp_parent, cfg):
    assert _codes(namkeen, bp_parent, cfg) == {"salt_high"}

def test_weight_loss_and_oats(oats, weight_loss_adult, cfg):
    assert _codes(oats, weight_loss_adult, cfg) == set()   # 389 kcal ≤ 400, grade A, 3.3 g protein/100 kcal < 5

def test_weight_loss_good_protein(curd, weight_loss_adult, cfg):
    p = replace(curd, per_100g=Nutrients(energy_kcal=100, protein_g=10, sugars_g=1, fat_g=1, sat_fat_g=0.5, salt_g=0.1))
    assert _codes(p, weight_loss_adult, cfg) == {"good_protein_density"}

def test_child_cola(cola, milk_allergic_child, cfg):       # 10.6*300/100 = 31.8 g vs 24 g limit (age 8) → 132%
    assert {"child_sugar_high", "child_caffeine"} <= _codes(cola, milk_allergic_child, cfg)

def test_infant_cola(cola, infant, cfg):
    assert {"infant_added_sugar"} <= _codes(cola, infant, cfg)

def test_no_age_skips_child_rules(cola, no_age, cfg):
    assert _codes(cola, no_age, cfg) == set()

def test_missing_sugar_for_diabetic_is_unknown(curd, diabetic_adult, cfg):
    p = replace(curd, per_100g=replace(curd.per_100g, sugars_g=None))
    assert ("nutrient_missing", Status.UNKNOWN) in _pairs(p, diabetic_adult, cfg)
```

Test helpers:
- `_codes` builds the inputs via `compute_nutriscore` and `check_claims`, then returns `{r.code for r in condition_reasons(...)}`.
- `_pairs` returns `(code, severity)` pairs.

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/scoring/test_conditions.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement `condition_reasons`** to the table, reading every number from `cfg.thresholds["conditions"]`.
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(scoring): condition, goal, child and infant rules`.

---

### Task 10: Report builder, member verdicts and the public `analyze()`

**Files:**
- Create: `apps/api/app/scoring/verdict.py`, `apps/api/tests/unit/scoring/test_verdict.py`
- Modify: `apps/api/app/scoring/__init__.py` (exports)

**Interfaces:**
- Consumes: everything from Tasks 2–9.
- Produces the **public API that Plan 2 imports**:

```python
@dataclass(frozen=True, slots=True)
class ProductReport:
    nutriscore: NutriScoreResult
    high_in: tuple[str, ...]
    allergens: Mapping[str, AllergenState]
    ingredients_known: bool
    diet_violations: Mapping[Diet, tuple[str, ...]]
    veg_mark_mismatch: bool
    hidden_sugars: tuple[str, ...]
    sodium_additives: tuple[str, ...]
    claims: tuple[ClaimCheck, ...]
    dropped_fields: tuple[str, ...]        # from Nutrients.sanitized()

@dataclass(frozen=True, slots=True)
class MemberVerdict:
    member_id: str
    status: Status
    reasons: tuple[Reason, ...]            # sorted by severity rank desc, then code

@dataclass(frozen=True, slots=True)
class AnalysisResult:
    report: ProductReport
    verdicts: tuple[MemberVerdict, ...]   # same order as input members
    def to_dict(self) -> dict[str, Any]    # JSON-safe: enums → .value, tuples → lists, Diet keys → str

def build_report(product: Product, cfg: ScoringConfig) -> ProductReport
def evaluate_member(product: Product, report: ProductReport, member: Member, cfg: ScoringConfig) -> MemberVerdict
def analyze(product: Product, members: Sequence[Member], cfg: ScoringConfig | None = None) -> AnalysisResult

# app/scoring/__init__.py exports:
# analyze, AnalysisResult, MemberVerdict, ProductReport, Product, Nutrients, Member,
# Category, Diet, Status, AllergenState, ClaimVerdict, Reason, load_config
```

How these work:
- `build_report` first replaces `product.per_100g` with `sanitized()` and records the dropped fields.
- `evaluate_member` combines `allergen_reasons + diet_reasons + condition_reasons`. The status is the highest-ranked severity, or `OK` when there are no reasons.

- [ ] **Step 1: Write failing golden tests**

```python
def test_family_on_sugar_free_biscuit(sf_biscuit, diabetic_adult, milk_allergic_child, weight_loss_adult):
    r = analyze(sf_biscuit, [diabetic_adult, milk_allergic_child, weight_loss_adult])
    assert [v.status for v in r.verdicts] == [Status.AVOID, Status.AVOID, Status.CAUTION]
    assert r.report.hidden_sugars == ("maltodextrin",)

def test_family_on_namkeen(namkeen, bp_parent, jain_adult, peanut_allergic):
    r = analyze(namkeen, [bp_parent, jain_adult, peanut_allergic])
    assert [v.status for v in r.verdicts] == [Status.AVOID] * 3
    assert r.report.nutriscore.grade == "E"

def test_curd(curd, diabetic_adult, vegan_adult, milk_allergic_child):
    r = analyze(curd, [diabetic_adult, vegan_adult, milk_allergic_child])
    assert [v.status for v in r.verdicts] == [Status.OK, Status.AVOID, Status.AVOID]

def test_unknown_product_for_allergic_member(no_ingredients, peanut_allergic):
    assert analyze(no_ingredients, [peanut_allergic]).verdicts[0].status == Status.UNKNOWN

def test_implausible_value_dropped_and_unknown(curd, diabetic_adult):
    p = replace(curd, per_100g=replace(curd.per_100g, sugars_g=250))
    r = analyze(p, [diabetic_adult])
    assert r.report.dropped_fields == ("sugars_g",) and r.verdicts[0].status == Status.UNKNOWN

def test_reasons_sorted_most_severe_first(sf_biscuit, diabetic_adult):
    reasons = analyze(sf_biscuit, [diabetic_adult]).verdicts[0].reasons
    assert [r.severity.rank for r in reasons] == sorted((r.severity.rank for r in reasons), reverse=True)

def test_to_dict_is_json_serialisable(namkeen, jain_adult):
    import json
    d = analyze(namkeen, [jain_adult]).to_dict()
    json.dumps(d)
    assert d["verdicts"][0]["status"] == "avoid" and d["report"]["diet_violations"]["jain"]
```

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/scoring/test_verdict.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement `verdict.py` and the `__init__.py` exports** to the Interfaces block.
- [ ] **Step 4: Run the full suite and lint**

Run: `uv run pytest -v && uv run ruff check app tests`
Expected: all tests pass, and ruff prints `All checks passed!`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/scoring apps/api/tests/unit/scoring
git commit -m "feat(scoring): product report, per-member verdicts and analyze() API"
```

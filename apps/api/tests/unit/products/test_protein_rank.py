"""Plan 9 Task 6 (P9-R11): the pure higher-protein ranking.

Candidates need a known protein per 100 kcal STRICTLY above the source's and a grade no worse
than the source's; `avoid` for the member is dropped; ok > caution > unknown, then protein
per 100 kcal (high first), then grade, then name; at most 5. Protein numbers come from the
engine's report.protein.
"""

import inspect

import pytest

from app import scoring
from app.features.products.alternatives import Candidate, rank_alternatives_by_protein

ADULT = scoring.Member(id="a", name="", age=30)
MILK_ALLERGIC = scoring.Member(id="m", name="", age=30, allergens=("milk",))
DIABETIC = scoring.Member(id="d", name="", age=50, conditions=("diabetes",))


def product(name, *, protein, kcal=100.0, sugars=1.0, ingredients=("rice flour", "salt")):
    return scoring.Product(
        name=name,
        per_100g=scoring.Nutrients(
            energy_kcal=kcal,
            protein_g=protein,
            carbs_g=10,
            sugars_g=sugars,
            fat_g=1,
            sat_fat_g=0.1,
            fiber_g=1,
            salt_g=0.1,
        ),
        ingredients=tuple(ingredients),
    )


def cand(name, *, grade, protein, **kw):
    return Candidate(product=product(name, protein=protein, **kw), grade=grade, payload={})


SOURCE = product("source", protein=5)  # 5 g per 100 kcal; grade computed by the engine


def _grade(p):
    return scoring.analyze(p, []).report.nutriscore.grade


def _names(result):
    items, _reason = result
    return [c.product.name for c in items]


def test_source_grade_is_known():
    assert _grade(SOURCE) is not None


def test_never_avoid_for_member():
    g = _grade(SOURCE)
    cands = [
        cand("milk shake", grade=g, protein=9, ingredients=("milk", "sugar")),
        cand("chana", grade=g, protein=8),
    ]
    assert _names(rank_alternatives_by_protein(SOURCE, cands, MILK_ALLERGIC)) == ["chana"]
    assert set(_names(rank_alternatives_by_protein(SOURCE, cands, ADULT))) == {
        "milk shake",
        "chana",
    }


def test_never_worse_grade():
    bar = "ABCDE".index(_grade(SOURCE))
    worse = "ABCDE"[min(bar + 1, 4)]
    better = "ABCDE"[max(bar - 1, 0)]
    cands = [
        cand("worse", grade=worse, protein=20),
        cand("ungraded", grade=None, protein=20),
        cand("same", grade=_grade(SOURCE), protein=6),
        cand("better", grade=better, protein=6),
    ]
    names = _names(rank_alternatives_by_protein(SOURCE, cands, ADULT))
    assert "ungraded" not in names and set(names) <= {"same", "better", "worse"}
    if worse != _grade(SOURCE):
        assert "worse" not in names


def test_strictly_more_protein_per_100kcal():
    g = _grade(SOURCE)
    cands = [
        cand("equal", grade=g, protein=5),
        cand("less", grade=g, protein=4),
        cand("more", grade=g, protein=5.1),
    ]
    assert _names(rank_alternatives_by_protein(SOURCE, cands, ADULT)) == ["more"]


def test_unknown_protein_excluded():
    g = _grade(SOURCE)
    cands = [cand("no protein", grade=g, protein=None), cand("no kcal", grade=g, protein=9, kcal=0)]
    items, reason = rank_alternatives_by_protein(SOURCE, cands, ADULT)
    assert items == [] and reason == "no_better_found"


def test_source_without_protein_or_grade():
    no_protein = product("p", protein=None)
    assert rank_alternatives_by_protein(no_protein, [], ADULT) == ([], "source_protein_unknown")
    ungraded = scoring.Product(name="u", per_100g=scoring.Nutrients(protein_g=5, energy_kcal=100))
    assert rank_alternatives_by_protein(ungraded, [], ADULT) == ([], "source_ungraded")


def test_order_status_then_protein():
    g = _grade(SOURCE)
    cands = [
        # Caution for a diabetic (sugar above the caution band), most protein.
        cand("sweet", grade=g, protein=12, sugars=6),
        cand("b-plain", grade=g, protein=7),
        cand("a-plain", grade=g, protein=7),
        cand("top", grade=g, protein=9),
    ]
    items, reason = rank_alternatives_by_protein(SOURCE, cands, DIABETIC)
    assert reason == "ok"
    statuses = [scoring.analyze(c.product, [DIABETIC]).verdicts[0].status.value for c in items]
    assert statuses == sorted(statuses, key=["ok", "caution", "unknown"].index)
    assert [c.product.name for c in items][-1] == "sweet"
    assert [c.product.name for c in items][:3] == ["top", "a-plain", "b-plain"]


def test_at_most_five():
    g = _grade(SOURCE)
    cands = [cand(f"c{i}", grade=g, protein=6 + i) for i in range(8)]
    names = _names(rank_alternatives_by_protein(SOURCE, cands, ADULT))
    assert names == ["c7", "c6", "c5", "c4", "c3"]


def test_defaults_to_primary_member():
    """The pure function always takes a member: the route passes member_id's member or the
    primary member (tests/api/products/test_protein_sort.py checks the route)."""
    param = inspect.signature(rank_alternatives_by_protein).parameters["member"]
    assert param.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        rank_alternatives_by_protein(SOURCE, [])  # type: ignore[call-arg]

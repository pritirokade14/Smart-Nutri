"""Side-by-side compare of two products (F9).

Which side is "better" per nutrient is a plain comparison of the engine-sanitised per-100 g
values (an implausible value is dropped, so it is ``unknown``); grades and member statuses
come from ``app.scoring.analyze``. Missing on either side is ``unknown``, never a win.
"""

from datetime import date
from typing import Literal

from app import scoring
from app.features.members.models import Member
from app.features.members.service import to_scoring_member
from app.features.products import service
from app.features.products.schemas import CompareBetter, CompareOut, CompareSide
from app.features.products.service import ProductLookup
from app.scoring.nutriscore import NutriScoreResult

Better = Literal["a", "b", "same", "unknown"]
LOWER_IS_BETTER = ("energy_kcal", "sugars_g", "salt_g", "sat_fat_g")
HIGHER_IS_BETTER = ("protein_g", "fiber_g")
_GRADES = ("A", "B", "C", "D", "E")


def _value(p: scoring.Product, key: str) -> float | None:
    n = p.per_100g
    return n.salt() if key == "salt_g" else getattr(n, key)


def _pick(a: float | None, b: float | None, *, lower: bool) -> Better:
    if a is None or b is None:
        return "unknown"
    a, b = round(a, 3), round(b, 3)
    if a == b:
        return "same"
    return "a" if (a < b) == lower else "b"


def compare(
    a: tuple[scoring.Product, NutriScoreResult], b: tuple[scoring.Product, NutriScoreResult]
) -> dict[str, Better]:
    """Per key: which side is better. Pure. Values are sanitised first (the engine's rule)."""
    pa, _ = a[0].sanitized()
    pb, _ = b[0].sanitized()
    out: dict[str, Better] = {}
    for key in LOWER_IS_BETTER:
        out[key] = _pick(_value(pa, key), _value(pb, key), lower=True)
    for key in HIGHER_IS_BETTER:
        out[key] = _pick(_value(pa, key), _value(pb, key), lower=False)
    ga, gb = a[1].grade, b[1].grade
    out["grade"] = _pick(
        None if ga is None else float(_GRADES.index(ga)),
        None if gb is None else float(_GRADES.index(gb)),
        lower=True,
    )
    return out


def _side(
    found: ProductLookup, result: scoring.AnalysisResult, member: scoring.Member | None
) -> CompareSide:
    out = service.to_product_out(found)
    return CompareSide(
        product_id=found.product_id,
        barcode=found.info.barcode or None,
        name=found.info.name or found.product.name,
        brand=found.info.brand,
        grade=result.report.nutriscore.grade,
        per_100g=out.per_100g,
        high_in=list(result.report.high_in),
        member_status=result.verdicts[0].status.value if member is not None else None,
        attribution=found.attribution,
    )


def compare_products(
    a: ProductLookup, b: ProductLookup, *, member: Member | None, today: date
) -> CompareOut:
    scoring_member = to_scoring_member(member, today=today) if member is not None else None
    members = [scoring_member] if scoring_member is not None else []
    ra = scoring.analyze(a.product, members)
    rb = scoring.analyze(b.product, members)
    better = compare((a.product, ra.report.nutriscore), (b.product, rb.report.nutriscore))
    return CompareOut(
        a=_side(a, ra, scoring_member),
        b=_side(b, rb, scoring_member),
        better=CompareBetter(**better),
    )

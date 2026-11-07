"""Nutrient sums for dishes and recipes (Plan 12 Task 3; spec 5.9; G8, G19). Pure, `Decimal`.

The rule that matters: a nutrient unknown on ANY part is never stored looking complete.
`sum_nutrients` adds the known parts and names the incomplete nutrients; `per_100_from` with
`strict=True` (dishes, diary snapshots) turns every incomplete nutrient into None, and with
`strict=False` (the recipe view) keeps the known-part value so the screen can say "at least".
A nutrient no part knows is None, never 0. Task 12 reuses this module.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from app import scoring

# = NutrientSnapshot (the diary entry's nutrient keys), fibre spelt `fibre_g`.
NUTRIENT_KEYS = (
    "energy_kcal",
    "sugars_g",
    "salt_g",
    "protein_g",
    "fat_g",
    "sat_fat_g",
    "carbs_g",
    "fibre_g",
)
_SALT_PER_SODIUM_MG = Decimal("2.5") / 1000


def _dec(value: float | Decimal | None) -> Decimal | None:
    return None if value is None else Decimal(repr(value)) if isinstance(value, float) else value


def snapshot_per_100(n: scoring.Nutrients) -> dict[str, Decimal | None]:
    """Per 100 g (or ml) in the diary's keys: the engine's sanitiser first (implausible values
    become None), salt from salt or sodium (the higher wins, as `Nutrients.salt()`), `fiber_g`
    as `fibre_g`. Unrounded."""
    clean, _ = n.sanitized()
    salts = []
    if clean.salt_g is not None:
        salts.append(_dec(clean.salt_g))
    if clean.sodium_mg is not None:
        salts.append(_dec(clean.sodium_mg) * _SALT_PER_SODIUM_MG)  # type: ignore[operator]
    return {
        "energy_kcal": _dec(clean.energy_kcal),
        "sugars_g": _dec(clean.sugars_g),
        "salt_g": max(salts) if salts else None,
        "protein_g": _dec(clean.protein_g),
        "fat_g": _dec(clean.fat_g),
        "sat_fat_g": _dec(clean.sat_fat_g),
        "carbs_g": _dec(clean.carbs_g),
        "fibre_g": _dec(clean.fiber_g),
    }


def _f(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def to_nutrients(per_100: Mapping[str, Decimal | None]) -> scoring.Nutrients:
    """Back to the engine's field names: `salt_g` set and `sodium_mg` None, `fibre_g` as
    `fiber_g`."""
    return scoring.Nutrients(
        energy_kcal=_f(per_100.get("energy_kcal")),
        protein_g=_f(per_100.get("protein_g")),
        carbs_g=_f(per_100.get("carbs_g")),
        sugars_g=_f(per_100.get("sugars_g")),
        fat_g=_f(per_100.get("fat_g")),
        sat_fat_g=_f(per_100.get("sat_fat_g")),
        fiber_g=_f(per_100.get("fibre_g")),
        salt_g=_f(per_100.get("salt_g")),
        sodium_mg=None,
        fvl_percent=None,
    )


@dataclass(frozen=True, slots=True)
class Amount:
    """``grams`` of an ingredient whose nutrients per 100 g are ``per_100`` (NUTRIENT_KEYS)."""

    grams: Decimal
    per_100: Mapping[str, Decimal | None]


@dataclass(frozen=True, slots=True)
class Sums:
    """``totals``: the sum of the KNOWN parts per nutrient (None when no part knows it).
    ``incomplete``: nutrients at least one part does not know, in NUTRIENT_KEYS order."""

    totals: dict[str, Decimal | None]
    incomplete: tuple[str, ...]


def sum_nutrients(amounts: Sequence[Amount]) -> Sums:
    totals: dict[str, Decimal | None] = {}
    incomplete: list[str] = []
    for key in NUTRIENT_KEYS:
        known = [a.grams * v / 100 for a in amounts if (v := a.per_100.get(key)) is not None]
        totals[key] = sum(known, Decimal(0)) if known else None
        if len(known) < len(amounts):
            incomplete.append(key)
    return Sums(totals, tuple(incomplete))


def per_100_from(sums: Sums, basis_weight_g: Decimal, *, strict: bool) -> dict[str, Decimal | None]:
    """The sums per 100 g of a finished food of ``basis_weight_g``. ``strict=True``: every
    incomplete nutrient is None. ``strict=False``: the known-part value (a lower bound)."""
    out: dict[str, Decimal | None] = {}
    for key in NUTRIENT_KEYS:
        total = sums.totals[key]
        if total is None or (strict and key in sums.incomplete):
            out[key] = None
        else:
            out[key] = total * 100 / basis_weight_g
    return out

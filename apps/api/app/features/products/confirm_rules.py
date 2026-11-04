"""What the confirm screen must ask the user before a label draft is saved (Ruling R21).

Single source of truth: `create_product` enforces a scan save with these helpers, and
`ProductDraft.confirm` (computed from the draft by `confirm_hints`) tells both clients what to
ask, using the SAME helpers. Clients render the hints; they never re-derive the rules.

Pure: no I/O. Works on any object shaped like a `ProductDraft` (see `DraftFacts`), so the
normaliser can call it while building a draft without an import cycle.

Rules (R14-R20):
- `sodium_unit_unconfirmed`: sodium printed without a unit on ANY column (R19), or printed as
  an implausibly low mg value with no salt to check it (`sodium_unit_suspect`, EF2). The user must
  pick the unit (`ProductCreate.sodium_unit`) whenever the saved sodium is not null; the pick
  confirms sodium, so sodium is never a tick.
- `withheld_fields`: engine fields stored only when listed in `confirmed_fields` (or, for
  sodium, when a unit is picked). The draft's `engine_withheld`, except that on a
  `basis_mismatch` the explicit `basis` answers the basis doubt; plus an upper-bound ("<X")
  protein or fibre on ANY printed column (R19.3); plus sodium when its unit is unconfirmed;
  plus every printed field a failed arithmetic check names (`checked_fields`, label accuracy
  v2), basis mismatch or not: picking a basis does not answer an arithmetic doubt.
- `needs_serving_confirmation`: a per-serving save, or any save of a `derived_from_serving`
  draft (R19.2), stores nutrients only when `serving_size_g` is confirmed.
- R18: a scanned serving size is stored only when `serving_size_g` is confirmed.
- `basis_required` (a `basis_mismatch` warning) and `category_required` (`category_unknown` or
  `category_check`): the client must not preselect. `ProductCreate` requires both fields on
  every save anyway, so a body without them is a 422.
- Columns (R20): a printed column is `per_serving` whenever it has engine values, and
  `per_100g` when it has engine values and the draft is not `derived_from_serving` (derived
  numbers were never printed). With `basis_mismatch` both bases are offered; if exactly one
  column is printed it is `shared` (shown whatever basis is picked: its basis is the doubt).
  Without it only one basis is offered: `per_serving` for a derived draft, else `per_100g`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from app.features.products.schemas import CONFIRMABLE_FIELDS, NUTRIENT_FIELDS, ConfirmableField

Basis = Literal["per_100g", "per_serving"]
BASES: tuple[Basis, ...] = ("per_100g", "per_serving")
UPPER_BOUND_FIELDS = ("protein_g", "fiber_g")  # an upper bound is no evidence of protein
CATEGORY_WARNINGS = ("category_unknown", "category_check")
# Label accuracy v2: a failed arithmetic check withholds the fields it involves (the printed
# ones). The normaliser's `engine_withheld` and these hints read the same map.
CHECK_FIELDS: dict[str, tuple[str, ...]] = {
    "energy_mismatch": ("energy_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g"),
    "kcal_kj_mismatch": ("energy_kcal",),
    "salt_sodium_mismatch": ("salt_g", "sodium_mg"),
    "fat_parts_mismatch": ("fat_g", "sat_fat_g"),
}
# "<code>:<path or field>" warnings that withhold the field they name (last path segment).
FIELD_CHECK_CODES = ("decimal_shift", "column_mismatch")
# "<code>:<column>.sodium_mg" warnings that make the user pick the sodium unit (mg or g).
SODIUM_UNIT_CODES = ("unit_unconfirmed", "sodium_unit_suspect")


class DraftFacts(Protocol):
    """The `ProductDraft` fields these rules read."""

    @property
    def warnings(self) -> Sequence[str]: ...
    @property
    def engine_withheld(self) -> Sequence[str]: ...
    @property
    def derived_from_serving(self) -> bool: ...
    @property
    def serving_size_g(self) -> float | None: ...
    @property
    def per_100g(self) -> object: ...
    @property
    def per_serving(self) -> object | None: ...


class ColumnConfirm(BaseModel):
    """What to ask when the user saves with this `basis` (`ProductCreate.basis`)."""

    printed: bool = Field(
        description=(
            "The draft column of this name holds printed engine values (`per_100g` of a "
            "`derived_from_serving` draft never does: those numbers were calculated)."
        )
    )
    shared: bool = Field(
        description=(
            "On a `basis_mismatch` draft, this is the only printed column: show its values "
            "whichever basis the user picks (its basis is the doubt)."
        )
    )
    confirm_fields: list[ConfirmableField] = Field(
        description=(
            "Fields that need an explicit tick (`ProductCreate.confirmed_fields`) when this "
            "basis is saved; an unticked one is stored as null. `serving_size_g`, when "
            "listed and unticked on a per-serving or derived save, makes every nutrient null. "
            "Sodium is never listed when `sodium_unit_required` (the unit pick confirms it)."
        )
    )
    sodium_unit_required: bool = Field(
        description=(
            "Show a mg/g picker for sodium: `ProductCreate.sodium_unit` must be `mg` or `g` "
            "(never null) whenever the saved sodium is not null, else 422 `body.sodium_unit`. "
            "Set when sodium was printed without a unit (`unit_unconfirmed`) or as an "
            "implausibly low mg value with no salt to check it (`sodium_unit_suspect`)."
        )
    )
    serving_required: bool = Field(
        description=(
            "Saving this basis stores nutrient values only with a confirmed `serving_size_g` "
            "(`needs_serving_confirmation`, R19): keep save disabled until the serving size "
            "is confirmed (ticked or edited). Server-side, an unconfirmed serving still "
            "stores every nutrient as null."
        )
    )


class ConfirmColumns(BaseModel):
    """The bases the user may save with; null = not offered for this draft."""

    per_100g: ColumnConfirm | None
    per_serving: ColumnConfirm | None


class DraftConfirm(BaseModel):
    """Server-computed confirm-screen hints (R21). Clients render these; they never
    re-derive the save rules. Computed from the draft itself, so always current."""

    basis_required: bool = Field(
        description="Basis in doubt: offer both columns and never preselect a basis."
    )
    category_required: bool = Field(
        description="Category in doubt: never preselect; the user must pick a category."
    )
    columns: ConfirmColumns


def _has_engine_values(column: object | None) -> bool:
    return column is not None and any(getattr(column, f, None) is not None for f in NUTRIENT_FIELDS)


def sodium_unit_unconfirmed(draft: DraftFacts) -> bool:
    """The sodium unit must be picked: sodium was printed without a unit on ANY column (R19),
    or printed as mg but implausibly low with no salt to check it (`sodium_unit_suspect`,
    EF2: most likely a g value read as mg)."""
    return any(
        f"{code}:{col}.sodium_mg" in draft.warnings for code in SODIUM_UNIT_CODES for col in BASES
    )


def checked_fields(warnings: Sequence[str]) -> set[str]:
    """Engine fields named by failed arithmetic checks (`CHECK_FIELDS`, `FIELD_CHECK_CODES`),
    printed or not: callers keep only the printed ones."""
    fields: set[str] = set()
    for warning in warnings:
        code, _, path = warning.partition(":")
        if code in CHECK_FIELDS:
            fields.update(CHECK_FIELDS[code])
        elif code in FIELD_CHECK_CODES and path:
            fields.add(path.rsplit(".", 1)[-1])
    return fields & set(NUTRIENT_FIELDS)


def withheld_fields(draft: DraftFacts) -> set[str]:
    """Engine fields held back from storage until the user confirms them (R13/R14/R17/R19,
    and the label accuracy v2 arithmetic checks)."""
    withheld = set() if "basis_mismatch" in draft.warnings else set(draft.engine_withheld)
    withheld |= {
        f for f in UPPER_BOUND_FIELDS for col in BASES if f"upper_bound:{col}.{f}" in draft.warnings
    }
    columns = (draft.per_100g, draft.per_serving)
    withheld |= {
        f
        for f in checked_fields(draft.warnings)
        if any(getattr(c, f, None) is not None for c in columns)
    }
    if sodium_unit_unconfirmed(draft):
        withheld.add("sodium_mg")
    return withheld


def needs_serving_confirmation(draft: DraftFacts, basis: Basis) -> bool:
    """Values that depend on the serving size (sent per serving, or derived from it by the
    normaliser, with or without a basis mismatch: R19) are stored only with a confirmed
    serving size."""
    return basis == "per_serving" or draft.derived_from_serving


def basis_required(draft: DraftFacts) -> bool:
    """Basis in doubt: a mismatch, or no column printed (the user chooses, as in manual
    entry; R22)."""
    return "basis_mismatch" in draft.warnings or not _printed_bases(draft)


def category_required(draft: DraftFacts) -> bool:
    return any(w in draft.warnings for w in CATEGORY_WARNINGS)


def printed(draft: DraftFacts, basis: Basis) -> bool:
    """The draft column of this name holds printed engine values (R20)."""
    if basis == "per_serving":
        return _has_engine_values(draft.per_serving)
    return not draft.derived_from_serving and _has_engine_values(draft.per_100g)


def _printed_bases(draft: DraftFacts) -> tuple[Basis, ...]:
    return tuple(b for b in BASES if printed(draft, b))


def offered_bases(draft: DraftFacts) -> tuple[Basis, ...]:
    """The bases the confirm screen offers (R20, R22): exactly the printed columns (a
    derived per-100 g column is never printed). Both when the basis is in doubt (mismatch,
    or nothing printed), so an unprinted column is never offered next to a printed one
    except on a mismatch."""
    if basis_required(draft):
        return BASES
    return _printed_bases(draft)


def confirm_fields(draft: DraftFacts, basis: Basis) -> list[str]:
    """Fields to tick when saving with `basis`, in `CONFIRMABLE_FIELDS` order."""
    fields = withheld_fields(draft)
    if sodium_unit_unconfirmed(draft):
        fields.discard("sodium_mg")  # the unit picker confirms it
    if needs_serving_confirmation(draft, basis) or draft.serving_size_g is not None:
        fields.add("serving_size_g")  # R18/R19
    return [f for f in CONFIRMABLE_FIELDS if f in fields]


def column_confirm(draft: DraftFacts, basis: Basis) -> ColumnConfirm:
    other: Basis = "per_100g" if basis == "per_serving" else "per_serving"
    is_printed = printed(draft, basis)
    return ColumnConfirm(
        printed=is_printed,
        shared=basis_required(draft) and is_printed and not printed(draft, other),
        confirm_fields=confirm_fields(draft, basis),  # type: ignore[arg-type]
        sodium_unit_required=sodium_unit_unconfirmed(draft),
        serving_required=needs_serving_confirmation(draft, basis),
    )


def confirm_hints(draft: DraftFacts) -> DraftConfirm:
    offered = offered_bases(draft)
    columns = {b: column_confirm(draft, b) if b in offered else None for b in BASES}
    return DraftConfirm(
        basis_required=basis_required(draft),
        category_required=category_required(draft),
        columns=ConfirmColumns(**columns),
    )


def placeholder_confirm() -> DraftConfirm:
    """Overwritten by `ProductDraft`'s validator; never served."""
    return DraftConfirm(
        basis_required=True,
        category_required=True,
        columns=ConfirmColumns(per_100g=None, per_serving=None),
    )

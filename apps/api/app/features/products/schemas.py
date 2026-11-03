from enum import StrEnum
from typing import Annotated, Any, Literal, get_args
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

_Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
_ShortText = Annotated[str, StringConstraints(max_length=200)]
# Caps sized to what real labels print (R17e); longer input is rejected, never truncated.
_Statement = Annotated[str, StringConstraints(max_length=4000)]
_Item = Annotated[str, StringConstraints(max_length=1000)]
MAX_INGREDIENT_ITEMS = 400


class NutrientsOut(BaseModel):
    energy_kcal: float | None
    protein_g: float | None
    carbs_g: float | None
    sugars_g: float | None
    fat_g: float | None
    sat_fat_g: float | None
    fiber_g: float | None
    salt_g: float | None
    sodium_mg: float | None


NutrientField = Literal[
    "energy_kcal",
    "protein_g",
    "carbs_g",
    "sugars_g",
    "fat_g",
    "sat_fat_g",
    "fiber_g",
    "salt_g",
    "sodium_mg",
]
NUTRIENT_FIELDS: tuple[str, ...] = get_args(NutrientField)
if NUTRIENT_FIELDS != tuple(NutrientsOut.model_fields):  # one list, kept in step
    raise RuntimeError("NutrientField must list NutrientsOut's fields in order")


class ProductOut(BaseModel):
    source: Literal["smartnutri", "openfoodfacts"]
    product_id: UUID | None
    barcode: str | None
    name: str | None
    brand: str | None
    image_url: str | None
    category: str
    per_100g: NutrientsOut
    serving_size_g: float | None
    ingredients: list[str]
    claims: list[str]
    attribution: str | None


class PublicProductOut(BaseModel):
    product: ProductOut
    # Product-level report from analyze(product, []); never contains member verdicts.
    report: dict
    score_label: Literal["calculated_by_smartnutri"]


ConfirmableField = Literal[
    "energy_kcal",
    "protein_g",
    "carbs_g",
    "sugars_g",
    "fat_g",
    "sat_fat_g",
    "fiber_g",
    "salt_g",
    "sodium_mg",
    "serving_size_g",
]
CONFIRMABLE_FIELDS: tuple[str, ...] = get_args(ConfirmableField)
if CONFIRMABLE_FIELDS != (*NUTRIENT_FIELDS, "serving_size_g"):
    raise RuntimeError("ConfirmableField must be NutrientField plus serving_size_g")


def _nutrient(description: str) -> Any:
    return Field(description=description)


class PrintedNutrients(BaseModel):
    """One nutrition-table column exactly as the pack prints it (see `ProductCreate.basis`).

    Numbers only, no arithmetic: the server converts the basis and the sodium unit. A value
    not printed (or blanked by the user) is null, never 0. The nine engine fields are
    required (send null when not printed); `added_sugars_g` and `trans_fat_g` are optional
    and shown only, never engine inputs.
    """

    energy_kcal: float | None = _nutrient("Energy in kcal.")
    protein_g: float | None = _nutrient("Protein in g.")
    carbs_g: float | None = _nutrient("Total carbohydrate in g.")
    sugars_g: float | None = _nutrient("Total sugars in g.")
    fat_g: float | None = _nutrient("Total fat in g.")
    sat_fat_g: float | None = _nutrient("Saturated fat in g.")
    fiber_g: float | None = _nutrient("Dietary fibre in g.")
    salt_g: float | None = _nutrient("Salt in g.")
    sodium_mg: float | None = _nutrient(
        "Sodium as the number printed, in the unit given by `ProductCreate.sodium_unit` "
        "(mg when that is null; the server converts g to mg)."
    )
    added_sugars_g: float | None = Field(default=None, description="Added sugars in g.")
    trans_fat_g: float | None = Field(default=None, description="Trans fat in g.")

    model_config = ConfigDict(allow_inf_nan=False)


class ProductCreate(BaseModel):
    """A product the user confirmed on the label-confirm screen, or typed by hand.

    **The server does all nutrient arithmetic; the client only transcribes what the pack
    prints and records the user's explicit choices.** The stored per-100 g values are:

    1. `nutrients` as sent, with `sodium_mg` multiplied by 1000 when `sodium_unit` is `g`;
    2. then, when `basis` is `per_serving`, every value x 100 / `serving_size_g`;
    3. then, for a scan save, values the draft holds back are set to null unless confirmed
       (`confirmed_fields`, below);
    4. then the engine's plausibility check runs on exactly the values that will be stored
       (422 `implausible_value`), including `serving_size_g` only when it will be stored or
       used for conversion. Values are never rounded.

    With `scan_id` the values come from that label scan (source `label`, the extraction
    confidence, which user edits never raise); without it the entry is manual (source
    `user`, confidence 1.0, values taken as typed). For a scan save the server re-runs its
    current normaliser on the stored raw extraction (R19), so the warnings it applies can be
    stricter than the draft the client showed; scans without a stored raw extraction use the
    stored draft. Text keeps its script (Devanagari stays Devanagari); only surrounding
    whitespace is trimmed and blank items are dropped.

    **Clients do not re-derive the rules below: render `ProductDraft.confirm` (R21), which
    the server computes with the same helpers that enforce them.** A body that honours the
    hints is stored in full; one that ignores them is a 422 or stores null for each field it
    did not confirm.

    Every request counts toward the account's daily `product_creates` limit (429
    `rate_limited`), including requests rejected with 422, so a client should fix the body
    before retrying rather than resend it.

    Scan-save rules (422 `validation_error` with `details.fields` naming the field):
    - `category` and `basis` are always required (the user must pick them; nothing defaults).
    - (R19) `sodium_unit` must be `mg` or `g` (not null) whenever the draft has ANY
      `unit_unconfirmed:*.sodium_mg` warning (either column, whichever `basis` is chosen) and
      `nutrients.sodium_mg` is not null; else 422 `["body.sodium_unit"]`. Listing `sodium_mg`
      in `confirmed_fields` never stands in for the unit. A non-null unit confirms sodium.
    - (R19) With `basis` `per_serving`, or whenever the draft was `derived_from_serving`
      (with or without `basis_mismatch`), every nutrient is stored only if `confirmed_fields`
      contains `serving_size_g` (the user checked the serving size); otherwise all are
      stored null and the serving size is neither used nor checked.
    - (R18) The stored `serving_size_g` is the sent value only if `confirmed_fields` contains
      `serving_size_g`; otherwise it is stored null (unknown) and the engine falls back to
      per-100 g. A manual entry (no `scan_id`) stores the serving size as typed.
    - On a `basis_mismatch` draft the explicit `basis` confirms the values sent. (R19) An
      upper-bound ("<X") protein or fibre on EITHER printed column is stored only if listed
      in `confirmed_fields`, and a unit-less sodium still needs `sodium_unit`.
    """

    scan_id: UUID | None = Field(
        default=None, description="The label scan this came from; null for manual entry."
    )
    barcode: str | None = Field(default=None, max_length=64)
    name: _Name
    brand: _ShortText | None = None
    category: Literal["general", "beverage", "water", "cheese", "fat"] = Field(
        description="Required: the user's explicit choice (drinks are judged on drink limits)."
    )
    basis: Literal["per_100g", "per_serving"] = Field(
        description=(
            "Required: which printed column `nutrients` was transcribed from. `per_100g` "
            "means per 100 g or 100 ml; `per_serving` means per `serving_size_g`, and the "
            "server converts to per 100 g."
        )
    )
    nutrients: PrintedNutrients = Field(
        description="The chosen column as printed. The server converts it (see `basis`)."
    )
    # Null default on purpose: generated clients serialise defaults, and a client-side
    # default of "mg" would be indistinguishable from the user picking mg.
    sodium_unit: Literal["mg", "g"] | None = Field(
        default=None,
        description=(
            "The unit of `nutrients.sodium_mg`: null means mg (the unit is printed, or this "
            "is a manual entry in mg). `g` is converted to mg by the server. Send the user's "
            "explicit pick (`mg` or `g`, never null) whenever the scan draft has any "
            "`unit_unconfirmed:*.sodium_mg` warning (either column, whatever the basis) and "
            "sodium is not null, else 422 `body.sodium_unit` (R19). A non-null unit "
            "confirms sodium; `confirmed_fields` never replaces it."
        ),
    )
    serving_size_g: float | None = Field(
        default=None,
        description=(
            "Serving size in g (or ml). Required when `basis` is `per_serving`. For a scan "
            "save it is used for conversion and stored only when `confirmed_fields` lists it "
            "(R18); otherwise it is stored as null, and is not plausibility-checked because "
            "it is neither stored nor used (R19). A manual entry stores it as typed."
        ),
    )
    ingredients: list[_Item] = Field(default=[], max_length=MAX_INGREDIENT_ITEMS)
    allergen_statement: _Statement | None = None
    may_contain_statement: _Statement | None = None
    claims: list[_ShortText] = Field(default=[], max_length=50)
    veg_mark: Literal["veg", "non_veg"] | None = None
    # Ruling R14 (+R17): fields the user explicitly confirmed on the confirm screen.
    confirmed_fields: list[ConfirmableField] = Field(
        default=[],
        max_length=len(CONFIRMABLE_FIELDS),
        description=(
            "Scan saves only: what the user explicitly confirmed. A nutrient the draft lists "
            'in `engine_withheld`, or an upper-bound ("<0.1 g") protein or fibre on either '
            "printed column (R19), is stored only when listed here, else null. "
            "`serving_size_g` confirms the serving size and is required for any value of a "
            "per-serving save or a `derived_from_serving` draft to be stored (R19); an "
            "unconfirmed scanned serving size is stored as null (R18). Listing `sodium_mg` "
            "never replaces `sodium_unit`."
        ),
    )

    @field_validator("brand", "allergen_statement", "may_contain_statement")
    @classmethod
    def _blank_is_none(cls, value: str | None) -> str | None:
        return (value.strip() or None) if value is not None else None

    @field_validator("ingredients", "claims")
    @classmethod
    def _drop_blank_items(cls, value: list[str]) -> list[str]:
        return [s for v in value if (s := v.strip())]


# --- alternatives, search and compare (Plan 6 T5/T6) ---------------------------------------


class NutriScoreGrade(StrEnum):
    """Nutri-Score grade, calculated by SmartNutri (never an FSSAI rating)."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class MemberStatus(StrEnum):
    """A member's verdict from the rules engine (never computed by clients)."""

    OK = "ok"
    CAUTION = "caution"
    UNKNOWN = "unknown"
    AVOID = "avoid"


class AlternativeOut(BaseModel):
    """A product in the same Open Food Facts category with a strictly better Nutri-Score
    (calculated by SmartNutri). Open it with ``products_get_by_barcode``."""

    barcode: str | None
    product_id: UUID | None
    name: str
    brand: str | None
    image_url: str | None
    grade: NutriScoreGrade
    sugars_g: float | None = Field(description="Per 100 g/ml; null if not on the label")
    high_in: list[str]
    member_status: MemberStatus | None = Field(
        description="The rules engine's verdict for member_id (only when member_id is given)"
    )
    attribution: str | None = Field(description='"attribution.off": credit Open Food Facts')


class AlternativesOut(BaseModel):
    items: list[AlternativeOut] = Field(
        description=(
            "At most 5: best grade first, then less sugar, then name. With member_id, never a "
            "product the engine rates avoid for that member, and ok before caution before "
            "unknown"
        )
    )
    reason: Literal["ok", "no_category", "no_better_found", "source_ungraded"] = Field(
        description="no_better_found also when every better product is avoid for member_id"
    )


class SearchHit(BaseModel):
    """Our own products first (``product_id``), then Open Food Facts (``barcode`` only: open
    with ``products_get_by_barcode``)."""

    product_id: UUID | None
    barcode: str | None
    name: str
    brand: str | None
    grade: NutriScoreGrade | None = Field(
        description="Nutri-Score calculated by SmartNutri; null if unknown"
    )
    source: Literal["ours", "off"]
    attribution: str | None = Field(description='"attribution.off" for Open Food Facts hits')


class BetterSide(StrEnum):
    A = "a"
    B = "b"
    SAME = "same"
    UNKNOWN = "unknown"


class CompareSide(BaseModel):
    product_id: UUID | None = Field(description="Our own product; null for Open Food Facts")
    barcode: str | None
    name: str
    brand: str | None
    grade: NutriScoreGrade | None
    per_100g: NutrientsOut
    high_in: list[str]
    member_status: MemberStatus | None = Field(
        description="The rules engine's verdict for member_id (only when member_id is given)"
    )
    attribution: str | None


class CompareBetter(BaseModel):
    """Which side is better: lower energy, sugars, salt and saturated fat; higher protein and
    fibre; grade A best. ``unknown`` when either side has no value (never a win)."""

    energy_kcal: BetterSide
    sugars_g: BetterSide
    salt_g: BetterSide
    sat_fat_g: BetterSide
    protein_g: BetterSide
    fiber_g: BetterSide
    grade: BetterSide


class CompareOut(BaseModel):
    a: CompareSide
    b: CompareSide
    better: CompareBetter

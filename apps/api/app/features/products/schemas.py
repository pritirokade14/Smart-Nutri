from typing import Annotated, Literal, get_args
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator

_Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
_ShortText = Annotated[str, StringConstraints(max_length=200)]
_LongText = Annotated[str, StringConstraints(max_length=2000)]
_Item = Annotated[str, StringConstraints(max_length=500)]


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


class ProductCreate(BaseModel):
    """A product the user confirmed on the label-confirm screen, or typed by hand.

    With ``scan_id`` the values come from that label scan's draft (source ``label``, the
    draft's extraction confidence); without it the entry is manual (source ``user``,
    confidence 1.0). Blank values are null, never 0. Text keeps its script (Devanagari stays
    Devanagari); only surrounding whitespace is trimmed and blank items are dropped.
    """

    scan_id: UUID | None = None  # None = manual entry
    barcode: str | None = Field(default=None, max_length=64)
    name: _Name
    brand: _ShortText | None = None
    category: Literal["general", "beverage", "water", "cheese", "fat"] = "general"
    per_100g: NutrientsOut
    serving_size_g: float | None = None
    ingredients: list[_Item] = Field(default=[], max_length=300)
    allergen_statement: _LongText | None = None
    may_contain_statement: _LongText | None = None
    claims: list[_ShortText] = Field(default=[], max_length=50)
    veg_mark: Literal["veg", "non_veg"] | None = None
    # Ruling R14: per_100g fields the user explicitly confirmed on the confirm screen. A value
    # the scan's draft withholds from the engine (e.g. "<0.1 g" protein, sodium with no
    # printed unit) is saved only when its field is listed here; otherwise it is saved as null.
    confirmed_fields: list[NutrientField] = Field(default=[], max_length=len(NUTRIENT_FIELDS))

    @field_validator("brand", "allergen_statement", "may_contain_statement")
    @classmethod
    def _blank_is_none(cls, value: str | None) -> str | None:
        return (value.strip() or None) if value is not None else None

    @field_validator("ingredients", "claims")
    @classmethod
    def _drop_blank_items(cls, value: list[str]) -> list[str]:
        return [s for v in value if (s := v.strip())]

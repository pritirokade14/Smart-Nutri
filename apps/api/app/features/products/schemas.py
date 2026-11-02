from typing import Literal
from uuid import UUID

from pydantic import BaseModel


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

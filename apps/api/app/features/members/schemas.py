"""Members API schemas (Plan 5 Task 5; rulings P2, P5-R6, R7, R12).

- `birth_year` is required on create and can't be cleared by PATCH (P2, P5-R7). The response
  has no `age`: the engine's youngest-age rule (R19) is the only age, computed at analysis.
- New members can't be `self`: the primary (the account holder) is auto-created (P5-R6).
- Allergens: a canonical key (any case) is stored as the key; anything else is free text,
  stored NFC-normalised and stripped (the engine normalises it further when matching).
  At most 20 (Ruling P8.3).
- `custom_alerts` are the engine's CUSTOM_ALERT_KEYS; anything else is a 422.
"""

import unicodedata
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
)

from app.core.time import today_ist
from app.scoring import CUSTOM_ALERT_KEYS

Relation = Literal["self", "child", "parent", "spouse", "other"]
NewRelation = Literal["child", "parent", "spouse", "other"]
DietIn = Literal["veg", "eggetarian", "vegan", "jain", "non_veg"]
Sex = Literal["female", "male", "other"]
ConditionIn = Literal["diabetes", "prediabetes", "pcos", "hypertension"]
GoalIn = Literal["healthy_eating", "weight_loss", "weight_gain"]
CustomAlert = Literal[CUSTOM_ALERT_KEYS]  # type: ignore[valid-type]

# Must equal the keys of app/scoring/data/allergens.yaml (tested).
CANONICAL_ALLERGENS: tuple[str, ...] = (
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
)

MAX_ALLERGENS = 20  # Ruling P8.3
ALLERGEN_MIN_LEN = 2
ALLERGEN_MAX_LEN = 40
BIRTH_YEAR_MIN = 1900

# Health fields: writing a non-empty value needs an active `health_data` consent (P5).
HEALTH_FIELDS: tuple[str, ...] = ("allergens", "conditions", "goal", "height_cm", "weight_kg")

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
BirthYear = Annotated[int, Field(ge=BIRTH_YEAR_MIN)]
HeightCm = Annotated[float, Field(ge=30, le=250)]
WeightKg = Annotated[float, Field(ge=2, le=300)]
Allergens = Annotated[list[str], Field(max_length=MAX_ALLERGENS)]


def _dedupe[T](items: list[T]) -> list[T]:
    return list(dict.fromkeys(items))


def normalise_allergens(values: list[str]) -> list[str]:
    """NFC-normalise and strip each entry, map canonical keys case-insensitively, dedupe
    (keep first), cap at MAX_ALLERGENS.

    NFC first (Ruling P8.3), so a composed and a decomposed spelling of the same text
    ("café", or a Devanagari nukta letter) are one allergen. Free text is otherwise kept as
    typed ("kiwi", "मूंगफली").
    """
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = unicodedata.normalize("NFC", raw).strip()
        if not ALLERGEN_MIN_LEN <= len(value) <= ALLERGEN_MAX_LEN:
            raise ValueError(
                f"each allergen must be {ALLERGEN_MIN_LEN}-{ALLERGEN_MAX_LEN} characters"
            )
        folded = value.casefold()
        if folded in CANONICAL_ALLERGENS:
            value = folded
        if folded in seen:
            continue
        seen.add(folded)
        out.append(value)
    if len(out) > MAX_ALLERGENS:
        raise ValueError(f"at most {MAX_ALLERGENS} allergens")
    return out


def _check_birth_year(value: int | None) -> int | None:
    if value is not None and value > today_ist().year:
        raise ValueError("birth_year can't be in the future")
    return value


class _MemberFields(BaseModel):
    @field_validator("birth_year", check_fields=False)
    @classmethod
    def _birth_year_not_future(cls, v: int | None) -> int | None:
        return _check_birth_year(v)

    @field_validator("allergens", check_fields=False)
    @classmethod
    def _allergens(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else normalise_allergens(v)

    @field_validator("conditions", "custom_alerts", check_fields=False)
    @classmethod
    def _unique(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else _dedupe(v)


class MemberIn(_MemberFields):
    """Create a family member. The account holder (relation `self`) already exists."""

    name: Name
    relation: NewRelation
    birth_year: BirthYear
    sex: Sex | None = None
    height_cm: HeightCm | None = None
    weight_kg: WeightKg | None = None
    diet: DietIn = "non_veg"
    allergens: Allergens = []
    conditions: list[ConditionIn] = []
    custom_alerts: list[CustomAlert] = []
    goal: GoalIn | None = None


class MemberPatch(_MemberFields):
    """Change only the fields sent. `relation` can't become `self`, or change on the primary.

    `null` clears `sex`, `height_cm`, `weight_kg` and `goal`. For every other field `null`
    means "unchanged" (the generated Dart client sends every field, unset ones as null), so
    `birth_year` can never be cleared.
    """

    name: Name | None = None
    relation: Relation | None = None
    birth_year: BirthYear | None = None
    sex: Sex | None = None
    height_cm: HeightCm | None = None
    weight_kg: WeightKg | None = None
    diet: DietIn | None = None
    allergens: Allergens | None = None
    conditions: list[ConditionIn] | None = None
    custom_alerts: list[CustomAlert] | None = None
    goal: GoalIn | None = None

    def changes(self) -> dict[str, object]:
        """The fields to write: those sent, minus nulls for fields that can't be cleared."""
        return {
            field: getattr(self, field)
            for field in sorted(self.model_fields_set)
            if field in NULLABLE_ON_PATCH or getattr(self, field) is not None
        }


# PATCH fields that `null` clears. Any other field sent as null is left unchanged.
NULLABLE_ON_PATCH = frozenset({"sex", "height_cm", "weight_kg", "goal"})


class MemberOut(BaseModel):
    id: UUID
    name: str
    relation: Relation
    birth_year: int | None  # None only for the auto-created primary until it is edited
    sex: Sex | None
    height_cm: float | None
    weight_kg: float | None
    diet: DietIn
    allergens: list[str]
    conditions: list[ConditionIn]
    custom_alerts: list[CustomAlert]
    goal: GoalIn | None
    is_primary: bool

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.members.schemas import (
    CANONICAL_ALLERGENS,
    ConditionIn,
    CustomAlert,
    DietIn,
    GoalIn,
)


class MeOut(BaseModel):
    id: UUID
    email: str | None
    display_name: str | None
    language: Literal["en", "hi", "mr"]
    created_at: datetime


# --- user types (Plan 9 Task 1, rulings P9-R1..R4) ---------------------------------------------
#
# A user type is presentation only (layout, defaults offered for confirmation, copy). It never
# changes a verdict, never reaches an LLM prompt and never goes to analytics (P9-R8).

UserType = Literal["health_condition", "family", "weight_loss", "gym", "allergy_diet", "eat_better"]
# Safety first (P9-R4): the default active mode is the chosen type that comes first here.
USER_TYPE_PRIORITY: tuple[UserType, ...] = (
    "allergy_diet",
    "health_condition",
    "family",
    "weight_loss",
    "gym",
    "eat_better",
)
# Saving one of these, or a health follow-up, needs an active `health_data` consent.
HEALTH_REVEALING_TYPES: frozenset[str] = frozenset(
    {"health_condition", "weight_loss", "allergy_diet"}
)
HEALTH_FOLLOW_UPS: frozenset[str] = frozenset({"conditions", "allergens", "diet"})
DEFAULT_TYPE: UserType = "eat_better"
MAX_USER_TYPES = 3

GymGoal = Literal["build_muscle", "lose_fat", "stay_fit"]
FamilyWith = Literal["children", "parents", "partner", "others"]
# The keys of app/scoring/data/allergens.yaml (CANONICAL_ALLERGENS is tested against them).
AllergenKey = Literal[CANONICAL_ALLERGENS]  # type: ignore[valid-type]

# Which type each follow-up belongs to. A follow-up without its type is a 422
# `follow_up_without_type`.
FOLLOW_UP_TYPE: dict[str, UserType] = {
    "conditions": "health_condition",
    "family_with": "family",
    "gym_goal": "gym",
    "allergens": "allergy_diet",
    "diet": "allergy_diet",
    "alerts": "eat_better",
}


def _unique[T](value: list[T] | None) -> list[T] | None:
    if value is not None and len(set(value)) != len(value):
        raise ValueError("items must be unique")
    return value


class FollowUps(BaseModel):
    """At most one short follow-up per type (decision 4). `weight_loss` has none.

    These are the user's answers, stored as given. They never change a member: pre-fill only
    suggests member changes, which the user confirms (Task 2).
    """

    model_config = ConfigDict(extra="forbid")

    conditions: list[ConditionIn] | None = Field(default=None, min_length=1, max_length=4)
    family_with: list[FamilyWith] | None = Field(default=None, max_length=4)
    gym_goal: GymGoal | None = None
    allergens: list[AllergenKey] | None = Field(default=None, max_length=11)
    diet: DietIn | None = None
    alerts: list[CustomAlert] | None = None

    @field_validator("conditions", "family_with", "allergens", "alerts")
    @classmethod
    def _lists_unique(cls, value: list[str] | None) -> list[str] | None:
        return _unique(value)

    def given(self) -> list[str]:
        """The follow-ups that were answered (non-null), in field order."""
        return [name for name in type(self).model_fields if getattr(self, name) is not None]


class UserTypesIn(BaseModel):
    """`types == []` is "Skip for now" (P9-R3). The order is the user's tap order."""

    types: list[UserType] = Field(max_length=MAX_USER_TYPES)
    follow_ups: FollowUps = Field(default_factory=FollowUps)

    @field_validator("types")
    @classmethod
    def _types_unique(cls, value: list[UserType]) -> list[UserType]:
        return _unique(value) or []


class ActiveTypeIn(BaseModel):
    active_type: UserType


PrefillField = Literal["conditions", "allergens", "diet", "goal", "custom_alerts"]


class PrefillChange(BaseModel):
    """One suggested change to the primary member. Never applied by the API: the client sends
    `value` in `PATCH /v1/members/{member_id}` only if the user confirms it."""

    field: PrefillField
    current: list[str] | str | None = Field(description="The primary member's value now")
    value: list[str] | str = Field(
        description="The FULL new value to send in MemberPatch if confirmed (never a removal)"
    )
    added: list[str] = Field(description="List fields: what is new (display); [] for diet/goal")
    reason: UserType = Field(description="Which type suggested it (display only)")


class PrefillSuggestion(BaseModel):
    """Suggestions for the account holder's own member, recomputed from the member on every
    read, so it is empty once the user has confirmed (Task 2, P9-R9)."""

    member_id: UUID = Field(description="Always the primary member (relation self)")
    changes: list[PrefillChange] = Field(
        description="[] means nothing to confirm: the client skips the review screen"
    )
    goal_choice: list[GoalIn] | None = Field(
        description=(
            "Goal conflict (weight loss and gym 'build muscle'): no goal change is in `changes`; "
            "the user picks one of these or neither"
        )
    )
    needs_health_consent: bool = Field(
        description="A change touches a health field and `health_data` is not active"
    )


class UserTypesOut(BaseModel):
    types: list[UserType] = Field(description="The user's tap order")
    follow_ups: FollowUps
    active_type: UserType = Field(
        description=(
            "Resolved: the stored value if still selected, else the highest-priority chosen "
            "type, else eat_better"
        )
    )
    answered: bool = Field(description="False until the first PUT: clients show the picker")
    answered_at: datetime | None
    prefill: PrefillSuggestion | None = Field(
        description="Suggested changes to the primary member (null until answered)"
    )
